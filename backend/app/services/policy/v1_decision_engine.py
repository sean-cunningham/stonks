from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import Settings
from app.core.enums import DecisionBucket, StrategyTrack
from app.models.account import Account
from app.models.active_position import ActivePosition
from app.models.candidate_trade import CandidateTrade
from app.models.event_analysis import EventAnalysis
from app.models.market_snapshot import MarketSnapshot
from app.models.recommendation_item import RecommendationItem
from app.models.trade_review import TradeReview
from app.repositories.recommendation_repository import RecommendationRepository
from app.services.ai.context_arbiter import (
    adversarial_context_agent,
    deterministic_context_arbiter,
    primary_context_agent,
)
from app.services.policy.v1_classifier import ScoreCard, classify_bucket, weighted_score
from app.services.policy.v1_hard_veto import evaluate_hard_veto
from app.services.strategy.v1_feature_engine import compute_v1_features
from app.services.strategy.v1_strategy_rules import SetupEvaluation
from app.services.strategy.v1_strategy_rules import evaluate_strategy_a_setups

log = logging.getLogger(__name__)


@dataclass
class DecisionOutcome:
    bucket: DecisionBucket
    strategy_track: StrategyTrack
    veto_reasons: list[str]
    veto_codes: list[str]
    score_card: ScoreCard | None
    weighted: float | None
    setup_family: str | None
    stop_price: float | None
    target_price: float | None
    explanation: str
    context_state: str
    context_action: str


class V1DecisionEngine:
    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._recommendations = RecommendationRepository(db)

    def evaluate(
        self,
        *,
        candidate: CandidateTrade,
        snapshot: MarketSnapshot | None,
        event_row: EventAnalysis | None,
    ) -> DecisionOutcome:
        now = utc_now()
        account = self._db.get(Account, 1)
        if not account:
            raise RuntimeError("primary account missing")
        open_positions = list(
            self._db.scalars(select(ActivePosition).where(ActivePosition.status == "open")).all()
        )
        features = compute_v1_features(snapshot) if snapshot else None
        primary = primary_context_agent(event_row, candidate.symbol)
        adversarial = adversarial_context_agent(event_row)
        arbiter = deterministic_context_arbiter(primary=primary, adversarial=adversarial)
        context_state = primary.context_state
        context_block = arbiter.blocked
        bullish = candidate.direction_bias == "long"
        if features:
            setup_eval = evaluate_strategy_a_setups(features, bullish=bullish, context_block=context_block)
        else:
            setup_eval = SetupEvaluation(
                ok=False,
                setup_family=None,
                direction=candidate.direction_bias,
                stop_price=None,
                target_price=None,
                r_to_target=0.0,
                reason_codes=["insufficient_feature_data"],
            )
        losses_today = _losses_today(self._db, now.date().isoformat())
        veto = evaluate_hard_veto(
            now=now,
            candidate=candidate,
            snapshot=snapshot,
            event_row=event_row,
            account=account,
            open_positions=open_positions,
            setup_eval=setup_eval,
            features=features,
            settings=self._settings,
            losses_today=losses_today,
            require_confirmation=arbiter.require_confirmation,
        )
        track = (
            StrategyTrack.STRATEGY_A
            if setup_eval.ok and setup_eval.setup_family in {"trend_continuation", "failed_breakout_rejection"}
            else StrategyTrack.STRATEGY_B
        )
        # Hard veto first.
        if not veto.ok and track == StrategyTrack.STRATEGY_A:
            return DecisionOutcome(
                bucket=DecisionBucket.REJECT,
                strategy_track=track,
                veto_reasons=veto.reasons,
                veto_codes=veto.codes,
                score_card=None,
                weighted=None,
                setup_family=setup_eval.setup_family,
                stop_price=setup_eval.stop_price,
                target_price=setup_eval.target_price,
                explanation="Hard veto failed for Strategy A.",
                context_state=context_state,
                context_action=arbiter.action,
            )
        card = _score_card(features=features, setup_ok=setup_eval.ok, context_state=context_state, snapshot=snapshot)
        score = weighted_score(card)
        bucket = classify_bucket(
            score=score,
            card=card,
            strategy_track=track.value,
            overnight_required=False,
            hard_reject=(not veto.ok and track != StrategyTrack.STRATEGY_B),
            recommend_context_uncertainty=context_state in {"watch", "caution"},
            recommend_outside_auto_risk=not veto.ok,
            recommend_event_driven=candidate.is_event_driven,
            recommend_thin_history=card.historical_support <= 3,
        )
        if track == StrategyTrack.STRATEGY_B and bucket == DecisionBucket.AUTO_EXECUTE:
            bucket = DecisionBucket.RECOMMEND_ONLY
        if bucket == DecisionBucket.RECOMMEND_ONLY:
            if not self._can_emit_recommendation(candidate.symbol):
                bucket = DecisionBucket.REJECT
                veto.reasons.append("recommendation_quota_exceeded")
                veto.codes.append("REC_QUOTA")
        expl = f"bucket={bucket.value} score={score:.2f} track={track.value} context={context_state}"
        log.info("decision %s symbol=%s setup=%s veto=%s", bucket.value, candidate.symbol, setup_eval.setup_family, veto.codes)
        return DecisionOutcome(
            bucket=bucket,
            strategy_track=track,
            veto_reasons=veto.reasons,
            veto_codes=veto.codes,
            score_card=card,
            weighted=score,
            setup_family=setup_eval.setup_family,
            stop_price=setup_eval.stop_price,
            target_price=setup_eval.target_price,
            explanation=expl,
            context_state=context_state,
            context_action=arbiter.action,
        )

    def _can_emit_recommendation(self, symbol: str) -> bool:
        rows = self._recommendations.list_by_status(status="suggested_for_review", limit=300)
        now = utc_now()
        today = now.date()
        today_rows = [r for r in rows if r.created_at.astimezone(UTC).date() == today]
        if len(today_rows) >= self._settings.paper_recommendation_max_per_day:
            return False
        per_symbol = [
            r
            for r in today_rows
            if str((r.affected_scope or {}).get("symbol", "")).upper() == symbol.upper()
        ]
        return len(per_symbol) < self._settings.paper_recommendation_max_per_symbol_per_day

    def create_recommendation_item(self, *, candidate: CandidateTrade, outcome: DecisionOutcome) -> RecommendationItem:
        payload = {
            "trade_family": outcome.setup_family or "strategy_b_candidate",
            "thesis": "Scored opportunity outside auto-execution gates.",
            "recommended_structure": candidate.strategy,
            "strikes_dte": (candidate.metadata_json or {}).get("option_contract"),
            "max_risk": f"{self._settings.paper_normal_risk_tier_pct:.2f}% account",
            "invalidation": f"stop={outcome.stop_price}",
            "target_logic": f"target={outcome.target_price}",
            "why_not_auto": outcome.veto_reasons or ["strategy_b_or_context"],
            "key_risks": ["context_uncertainty", "execution_conditions", "event_risk"],
            "confidence_label": "medium" if (outcome.weighted or 0) >= 26 else "low",
            "symbol": candidate.symbol,
        }
        row = RecommendationItem(
            created_at=utc_now(),
            status="suggested_for_review",
            title=f"Recommend-only candidate {candidate.symbol}",
            evidence_summary=outcome.explanation,
            confidence=min(0.95, max(0.1, (outcome.weighted or 0) / 40.0)),
            affected_scope={"scope": "symbol", "symbol": candidate.symbol, "setup_family": outcome.setup_family},
            suggested_parameter_delta=payload,
            trade_review_id=None,
        )
        return self._recommendations.create(row)


def _score_card(
    *,
    features,
    setup_ok: bool,
    context_state: str,
    snapshot: MarketSnapshot | None,
) -> ScoreCard:
    liq = 5
    if snapshot:
        liq = 5 if (snapshot.spread_bps or 999) <= 10 else 3
        liq = min(liq, 4 if (snapshot.volume or 0) >= 300000 else 2)
    regime = 5 if features and features.regime.name in {"TREND_UP", "TREND_DOWN"} else 2
    context = 5 if context_state == "ignore" else (4 if context_state == "watch" else (3 if context_state == "caution" else 1))
    execution = 4 if liq >= 3 else 2
    historical = 3
    setup = 5 if setup_ok else 2
    return ScoreCard(
        setup_quality=setup,
        regime_fit=regime,
        liquidity_quality=liq,
        event_context_safety=context,
        execution_quality=execution,
        historical_support=historical,
    )


def _losses_today(db: Session, day_iso: str) -> int:
    q = select(func.count()).select_from(TradeReview).where(
        func.date(TradeReview.created_at) == day_iso,
        TradeReview.realized_pnl_dollars < 0,
    )
    return int(db.scalar(q) or 0)
