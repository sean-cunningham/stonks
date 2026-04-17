from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import Settings, get_settings
from app.repositories.account_repository import AccountRepository
from app.repositories.bot_state_repository import BotStateRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.decision_snapshot_repository import DecisionSnapshotRepository
from app.repositories.event_analysis_repository import EventAnalysisRepository
from app.repositories.position_repository import PositionRepository
from app.repositories.rejection_repository import RejectionRepository
from app.repositories.trade_repository import TradeRepository
from app.repositories.x_enrichment_repository import XEnrichmentRepository
from app.schemas.account import BalancesRead
from app.schemas.active_position import ActivePositionRead
from app.schemas.approved_trade import ApprovedTradeRead
from app.schemas.candidate_trade import CandidateTradeRead
from app.schemas.decision_snapshot import DecisionSnapshotRead
from app.schemas.event_analysis import EventAnalysisRead
from app.schemas.rejected_trade import RejectedTradeRead
from app.schemas.analytics import AnalyticsCompactBlock
from app.schemas.status import BotStateRead, FillRead, StatusResponse
from app.schemas.x_enrichment import XEnrichmentRead
from app.services.analytics.analytics_engine import compact_summary_for_status, load_all_reviews

router = APIRouter(tags=["status"])


def _iso(dt) -> str:
    return dt.isoformat() if dt else ""


def build_status_response(db: Session, settings: Settings | None = None) -> StatusResponse:
    if settings is None:
        settings = get_settings()
    acc_repo = AccountRepository(db)
    bot_repo = BotStateRepository(db)
    pos_repo = PositionRepository(db)
    trades = TradeRepository(db)
    cand_repo = CandidateRepository(db)
    rej_repo = RejectionRepository(db)
    ev_repo = EventAnalysisRepository(db)
    x_repo = XEnrichmentRepository(db)
    d_repo = DecisionSnapshotRepository(db)

    acc = acc_repo.ensure_primary(settings.bot_default_starting_cash)
    bot = bot_repo.get()
    in_trades = acc_repo.funds_in_open_positions()
    open_pos = pos_repo.list_open()

    balances = BalancesRead(
        cash=acc.cash_balance,
        in_trades=in_trades,
        total=acc.equity,
        currency=acc.currency,
    )

    def pos_read(p) -> ActivePositionRead:
        return ActivePositionRead(
            id=p.id,
            symbol=p.symbol,
            strategy=p.strategy,
            status=p.status,
            quantity=p.quantity,
            average_entry_price=p.average_entry_price,
            market_value=p.market_value,
            unrealized_pnl=p.unrealized_pnl,
            initial_stop_price=p.initial_stop_price,
            emergency_premium_stop_pct=p.emergency_premium_stop_pct,
            current_trailing_stop=p.current_trailing_stop,
            breakeven_armed=p.breakeven_armed,
            partial_exit_taken=p.partial_exit_taken,
            partial_exit_qty=p.partial_exit_qty,
            thesis_expires_at=_iso(p.thesis_expires_at) if p.thesis_expires_at else None,
            high_water_mark_price=p.high_water_mark_price,
            low_water_mark_price=p.low_water_mark_price,
            reached_1r=p.reached_1r,
            reached_1_5r=p.reached_1_5r,
            reached_2r=p.reached_2r,
            opened_at=_iso(p.opened_at),
            closed_at=_iso(p.closed_at) if p.closed_at else None,
            legs=p.legs,
        )

    def at_read(t) -> ApprovedTradeRead:
        return ApprovedTradeRead(
            id=t.id,
            candidate_trade_id=t.candidate_trade_id,
            event_analysis_id=t.event_analysis_id,
            status=t.status,
            created_at=_iso(t.created_at),
            risk_snapshot=t.risk_snapshot,
            policy_trace=t.policy_trace,
        )

    def fill_read(f) -> FillRead:
        return FillRead(
            id=f.id,
            active_position_id=f.active_position_id,
            side=f.side,
            quantity=f.quantity,
            price=f.price,
            fee=f.fee,
            is_partial=f.is_partial,
            created_at=_iso(f.created_at),
        )

    def ev_read(e) -> EventAnalysisRead:
        return EventAnalysisRead(
            id=e.id,
            symbol=e.symbol,
            event_type=e.event_type,
            event_source_tier=e.event_source_tier,
            materiality_score=e.materiality_score,
            surprise_score=e.surprise_score,
            direction_bias=e.direction_bias,
            confidence_score=e.confidence_score,
            time_horizon=e.time_horizon,
            priced_in_risk=e.priced_in_risk,
            narrative_summary=e.narrative_summary,
            key_evidence_points=e.key_evidence_points,
            tradeability_flag=e.tradeability_flag,
            recommended_strategy=e.recommended_strategy,
            validation_ok=e.validation_ok,
            escalation_used=e.escalation_used,
            setup_score=e.setup_score,
            reason_codes=e.reason_codes,
            created_at=_iso(e.created_at),
        )

    def cand_read(c) -> CandidateTradeRead:
        return CandidateTradeRead(
            id=c.id,
            symbol=c.symbol,
            strategy=c.strategy,
            candidate_kind=c.candidate_kind,
            direction_bias=c.direction_bias,
            legs=c.legs,
            is_event_driven=c.is_event_driven,
            setup_type=c.setup_type,
            setup_score=c.setup_score,
            reason_codes=c.reason_codes,
            confirmation_state=c.confirmation_state,
            event_id=c.event_id,
            event_analysis_id=c.event_analysis_id,
            created_at=_iso(c.created_at),
            notes=c.notes,
        )

    def x_read(x) -> XEnrichmentRead:
        return XEnrichmentRead(
            id=x.id,
            symbol=x.symbol,
            provider=x.provider,
            model_name=x.model_name,
            sentiment_bias=x.sentiment_bias,
            acceleration_flag=x.acceleration_flag,
            rumor_risk_flag=x.rumor_risk_flag,
            confidence_score=x.confidence_score,
            summary=x.summary,
            evidence_points=x.evidence_points,
            event_analysis_id=x.event_analysis_id,
            candidate_trade_id=x.candidate_trade_id,
            created_at=_iso(x.created_at),
        )

    def rej_read(r) -> RejectedTradeRead:
        return RejectedTradeRead(
            id=r.id,
            candidate_trade_id=r.candidate_trade_id,
            event_analysis_id=r.event_analysis_id,
            reasons=r.reasons,
            rule_codes=r.rule_codes,
            detail=r.detail,
            created_at=_iso(r.created_at),
        )

    def dec_read(d) -> DecisionSnapshotRead:
        return DecisionSnapshotRead(
            id=d.id,
            created_at=_iso(d.created_at),
            symbol=d.symbol,
            candidate_trade_id=d.candidate_trade_id,
            approved_trade_id=d.approved_trade_id,
            bucket=d.bucket,
            strategy_track=d.strategy_track,
            hard_vetoes=d.hard_vetoes,
            hard_veto_codes=d.hard_veto_codes,
            scores=d.scores,
            weighted_score=d.weighted_score,
            explanation=d.explanation,
        )

    return StatusResponse(
        bot=BotStateRead(
            state=bot.state,
            pause_reason=bot.pause_reason,
            cooldown_until=_iso(bot.cooldown_until) if bot.cooldown_until else None,
        ),
        balances=balances,
        active_positions=[pos_read(p) for p in open_pos],
        recent_trades=[at_read(t) for t in trades.list_recent_approved(15)],
        recent_fills=[fill_read(f) for f in trades.list_recent_fills(20)],
        recent_event_analyses=[ev_read(e) for e in ev_repo.list_recent(10)],
        recent_x_enrichments=[x_read(x) for x in x_repo.list_recent(10)],
        recent_candidates=[cand_read(c) for c in cand_repo.list_recent(15)],
        recent_rejections=[rej_read(r) for r in rej_repo.list_recent(15)],
        recent_decisions=[dec_read(d) for d in d_repo.list_recent(20)],
        latest_account_snapshot_at=_iso(acc.updated_at),
        realized_pnl=acc.realized_pnl,
        unrealized_pnl=acc.unrealized_pnl,
        analytics_compact=AnalyticsCompactBlock(**compact_summary_for_status(load_all_reviews(db))),
    )


@router.get("/status", response_model=StatusResponse)
def get_status(db: Session = Depends(get_db)) -> StatusResponse:
    return build_status_response(db, get_settings())
