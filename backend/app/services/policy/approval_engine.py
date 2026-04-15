from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import Settings
from app.core.enums import AppMode, DecisionBucket
from app.models.active_position import ActivePosition
from app.models.candidate_trade import CandidateTrade
from app.models.event_analysis import EventAnalysis
from app.models.market_snapshot import MarketSnapshot
from app.repositories.bot_state_repository import BotStateRepository
from app.repositories.decision_snapshot_repository import DecisionSnapshotRepository
from app.repositories.rejection_repository import RejectionRepository
from app.repositories.trade_repository import TradeRepository
from app.services.policy.blackout_rules import BlackoutConfig, in_no_new_trades_window
from app.services.policy.v1_decision_engine import V1DecisionEngine


class ApprovalEngine:
    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._rej = RejectionRepository(db)
        self._tr = TradeRepository(db)
        self._snapshots = DecisionSnapshotRepository(db)

    def try_approve(self, candidate_id: int) -> tuple[str, int | None]:
        """Returns ('approved', trade_id) or ('rejected', rejection_id) or ('recommend_only', recommendation_id)."""
        cand = self._db.get(CandidateTrade, candidate_id)
        if not cand:
            r = self._rej.create(reasons=["candidate not found"], rule_codes=["NOT_FOUND"])
            return "rejected", r.id

        snap: MarketSnapshot | None = None
        if cand.market_snapshot_id:
            snap = self._db.get(MarketSnapshot, cand.market_snapshot_id)

        event_row: EventAnalysis | None = None
        if cand.event_analysis_id:
            event_row = self._db.get(EventAnalysis, cand.event_analysis_id)

        bot = BotStateRepository(self._db).get()
        if not bot:
            r = self._rej.create(
                reasons=["missing bot state"],
                rule_codes=["STATE"],
                candidate_trade_id=cand.id,
            )
            return "rejected", r.id
        if bot.state != "running":
            r = self._rej.create(
                reasons=["bot not running"],
                rule_codes=["BOT_NOT_RUNNING"],
                candidate_trade_id=cand.id,
            )
            return "rejected", r.id

        open_rows = list(
            self._db.scalars(
                select(ActivePosition).where(ActivePosition.status == "open"),
            ).all(),
        )
        dec = V1DecisionEngine(self._db, self._settings).evaluate(
            candidate=cand,
            snapshot=snap,
            event_row=event_row,
        )
        if self._settings.app_mode != AppMode.MOCK:
            cfg = BlackoutConfig(
                minutes_before_close=self._settings.bot_no_new_trades_minutes_before_close,
            )
            blackout = in_no_new_trades_window(utc_now(), cfg)
            if blackout and dec.bucket == DecisionBucket.AUTO_EXECUTE:
                dec.bucket = DecisionBucket.REJECT
                dec.veto_reasons.append("blackout_near_close")
                dec.veto_codes.append("BLACKOUT")

        if dec.bucket == DecisionBucket.REJECT:
            r = self._rej.create(
                reasons=dec.veto_reasons or ["rule_reject"],
                rule_codes=dec.veto_codes or ["REJECT"],
                candidate_trade_id=cand.id,
                event_analysis_id=cand.event_analysis_id,
            )
            self._snapshots.create(
                symbol=cand.symbol,
                candidate_trade_id=cand.id,
                event_analysis_id=cand.event_analysis_id,
                approved_trade_id=None,
                bucket=dec.bucket.value,
                strategy_track=dec.strategy_track.value,
                hard_vetoes=dec.veto_reasons,
                hard_veto_codes=dec.veto_codes,
                scores=dec.score_card.__dict__ if dec.score_card else None,
                weighted_score=dec.weighted,
                market_state_json={"snapshot_id": snap.id if snap else None},
                option_state_json=(snap.extra or {}).get("option_contract", {}) if snap else {},
                risk_state_json={"open_positions": len(open_rows)},
                context_state_json={"state": dec.context_state, "action": dec.context_action},
                historical_state_json={},
                order_instruction_json=None,
                explanation=dec.explanation,
            )
            return "rejected", r.id

        if dec.bucket == DecisionBucket.RECOMMEND_ONLY:
            rec = V1DecisionEngine(self._db, self._settings).create_recommendation_item(
                candidate=cand,
                outcome=dec,
            )
            self._snapshots.create(
                symbol=cand.symbol,
                candidate_trade_id=cand.id,
                event_analysis_id=cand.event_analysis_id,
                approved_trade_id=None,
                bucket=dec.bucket.value,
                strategy_track=dec.strategy_track.value,
                hard_vetoes=dec.veto_reasons,
                hard_veto_codes=dec.veto_codes,
                scores=dec.score_card.__dict__ if dec.score_card else None,
                weighted_score=dec.weighted,
                market_state_json={"snapshot_id": snap.id if snap else None},
                option_state_json=(snap.extra or {}).get("option_contract", {}) if snap else {},
                risk_state_json={"open_positions": len(open_rows)},
                context_state_json={"state": dec.context_state, "action": dec.context_action},
                historical_state_json={},
                order_instruction_json={
                    "action": "recommend_only",
                    "setup_family": dec.setup_family,
                    "stop_price": dec.stop_price,
                    "target_price": dec.target_price,
                },
                explanation=dec.explanation,
            )
            return "recommend_only", rec.id

        at = self._tr.create_approved(
            candidate_trade_id=cand.id,
            event_analysis_id=cand.event_analysis_id,
            status="pending",
            risk_snapshot={"max_risk_pct": self._settings.paper_normal_risk_tier_pct},
            policy_trace={
                "bucket": dec.bucket.value,
                "score": dec.weighted,
                "setup_family": dec.setup_family,
                "context_state": dec.context_state,
            },
        )
        self._snapshots.create(
            symbol=cand.symbol,
            candidate_trade_id=cand.id,
            event_analysis_id=cand.event_analysis_id,
            approved_trade_id=at.id,
            bucket=dec.bucket.value,
            strategy_track=dec.strategy_track.value,
            hard_vetoes=dec.veto_reasons,
            hard_veto_codes=dec.veto_codes,
            scores=dec.score_card.__dict__ if dec.score_card else None,
            weighted_score=dec.weighted,
            market_state_json={"snapshot_id": snap.id if snap else None},
            option_state_json=(snap.extra or {}).get("option_contract", {}) if snap else {},
            risk_state_json={"open_positions": len(open_rows)},
            context_state_json={"state": dec.context_state, "action": dec.context_action},
            historical_state_json={},
            order_instruction_json={
                "action": "auto_execute",
                "setup_family": dec.setup_family,
                "stop_price": dec.stop_price,
                "target_price": dec.target_price,
            },
            explanation=dec.explanation,
        )
        return "approved", at.id
