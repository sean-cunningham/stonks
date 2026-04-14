"""Build and persist trade review rows when positions close (analytics only)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.active_position import ActivePosition
from app.models.approved_trade import ApprovedTrade
from app.models.candidate_trade import CandidateTrade
from app.models.event_analysis import EventAnalysis
from app.models.trade_review import TradeReview
from app.models.x_enrichment import XEnrichment
from app.repositories.trade_review_repository import TradeReviewRepository
from app.services.analytics.exit_classifier import classify_exit
from app.services.analytics.shadow_experiments import run_shadow_experiments_for_review
from app.services.execution.pnl_engine import update_unrealized

if TYPE_CHECKING:
    from app.core.config import Settings

log = logging.getLogger(__name__)


def _risk_dollars(position: ActivePosition) -> float:
    entry = position.average_entry_price
    risk_per = abs(entry - (position.initial_stop_price or entry * 0.95))
    if risk_per <= 0:
        risk_per = entry * 0.05
    return risk_per * 100.0 * max(1, position.quantity)


def _trade_family(setup_type: str | None) -> str:
    if setup_type == "anticipatory_macro_event":
        return "anticipatory"
    return "confirmed"


def _had_thenewsapi(ev: EventAnalysis | None) -> bool:
    if not ev or not ev.normalized_event_id:
        return False
    return ev.normalized_event_id.lower().startswith("thenewsapi|")


def persist_trade_review_on_close(
    db: Session,
    position: ActivePosition,
    exit_mark_price: float,
    exit_reason: str | None,
    *,
    settings: Settings,
) -> TradeReview | None:
    repo = TradeReviewRepository(db)
    if repo.get_by_approved_trade_id(position.approved_trade_id):
        return None

    approved = db.get(ApprovedTrade, position.approved_trade_id)
    if not approved:
        log.warning("trade review skip: missing approved trade %s", position.approved_trade_id)
        return None

    cand = db.get(CandidateTrade, approved.candidate_trade_id)
    ev: EventAnalysis | None = None
    if approved.event_analysis_id:
        ev = db.get(EventAnalysis, approved.event_analysis_id)
    if not ev and cand and cand.event_analysis_id:
        ev = db.get(EventAnalysis, cand.event_analysis_id)

    update_unrealized(position, exit_mark_price)
    realized = float(position.unrealized_pnl or 0.0)
    rd = _risk_dollars(position)
    realized_r = (realized / rd) if rd > 1e-9 else None

    entry = position.average_entry_price
    qty = max(1, position.quantity)
    mult = 100
    hw = position.high_water_mark_price if position.high_water_mark_price is not None else entry
    lw = position.low_water_mark_price if position.low_water_mark_price is not None else entry
    mfe = max(0.0, (hw - entry) * mult * qty)
    mae = max(0.0, (entry - lw) * mult * qty)

    had_x = False
    if cand:
        had_x = db.scalar(select(XEnrichment.id).where(XEnrichment.candidate_trade_id == cand.id).limit(1)) is not None
    if not had_x and ev:
        had_x = db.scalar(select(XEnrichment.id).where(XEnrichment.event_analysis_id == ev.id).limit(1)) is not None

    policy_trace = approved.policy_trace
    rule_ok = True
    if isinstance(policy_trace, dict) and policy_trace.get("manual_override"):
        rule_ok = False

    opened = position.opened_at
    closed = position.closed_at or utc_now()
    hold_secs = int((closed - opened).total_seconds()) if opened and closed else None

    setup_type = cand.setup_type if cand else None
    label, expl = classify_exit(
        realized_pnl_dollars=realized,
        mfe_dollars=mfe,
        mae_dollars=mae,
        exit_reason=exit_reason,
        hit_plus_1r=position.reached_1r,
        hit_plus_2r=position.reached_2r,
    )

    row = TradeReview(
        created_at=utc_now(),
        approved_trade_id=approved.id,
        candidate_trade_id=cand.id if cand else None,
        active_position_id=position.id,
        event_analysis_id=ev.id if ev else None,
        symbol=position.symbol,
        setup_type=setup_type,
        setup_score=cand.setup_score if cand else None,
        confirmation_state=cand.confirmation_state if cand else None,
        event_id=cand.event_id if cand else None,
        event_type=ev.event_type if ev else None,
        trade_family=_trade_family(setup_type),
        entry_price=entry,
        exit_price=exit_mark_price,
        exit_reason=exit_reason,
        quantity=qty,
        realized_pnl_dollars=realized,
        realized_r_multiple=realized_r,
        mfe_dollars=mfe,
        mae_dollars=mae,
        holding_seconds=hold_secs,
        hit_plus_1r=position.reached_1r,
        hit_plus_1_5r=position.reached_1_5r,
        hit_plus_2r=position.reached_2r,
        rule_adherence_ok=rule_ok,
        had_x_enrichment=had_x,
        had_thenewsapi_supplement=_had_thenewsapi(ev),
        reason_codes_snapshot=list(cand.reason_codes) if cand and cand.reason_codes else None,
        policy_trace_snapshot=dict(policy_trace) if isinstance(policy_trace, dict) else None,
        exit_quality_label=label,
        exit_quality_explanation=expl,
        journaling_version=1,
    )
    repo.create(row)
    run_shadow_experiments_for_review(db, row, settings=settings)
    return row
