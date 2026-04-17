from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.api.analytics import build_analytics_summary, build_recommendation_reads, build_setups_slice
from app.api.status import build_status_response
from app.core.config import Settings
from app.core.enums import AppMode
from app.jobs.scheduler import ensure_background_jobs_started, maybe_stop_background_jobs
from app.repositories.bot_state_repository import BotStateRepository
from app.schemas.strategy_dashboard import StrategyDashboardBundle, StrategyStatusBlock
from app.strategies.registry import STRATEGY_EVENT_EDGE_V1, get_strategy_meta
from app.strategies.spy_0dte_scalper.live_readiness import build_event_edge_runtime_health


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


def event_edge_status_block(db: Session, settings: Settings) -> StrategyStatusBlock:
    sr = build_status_response(db, settings)
    meta = get_strategy_meta(STRATEGY_EVENT_EDGE_V1)
    assert meta is not None
    open_id = sr.active_positions[0].id if sr.active_positions else None
    paper_only = settings.app_mode != AppMode.FULL_ANALYSIS
    return StrategyStatusBlock(
        strategy_id=STRATEGY_EVENT_EDGE_V1,
        display_name=meta.display_name,
        state=sr.bot.state,
        pause_reason=sr.bot.pause_reason,
        cooldown_until=sr.bot.cooldown_until,
        paper_only=paper_only,
        app_mode=str(settings.app_mode.value),
        open_position_id=open_id,
        live_candidate_pipeline_enabled=settings.live_candidate_pipeline_enabled,
        spy_scalper_synthetic_blocked=None,
        spy_scalper_synthetic_block_reason=None,
    )


def event_edge_enable(db: Session, settings: Settings) -> StrategyStatusBlock:
    BotStateRepository(db).set_state("running", pause_reason=None)
    ensure_background_jobs_started(settings)
    return event_edge_status_block(db, settings)


def event_edge_disable(db: Session, settings: Settings) -> StrategyStatusBlock:
    BotStateRepository(db).set_state("stopped", pause_reason=None)
    maybe_stop_background_jobs()
    return event_edge_status_block(db, settings)


def event_edge_get_config(db: Session, settings: Settings) -> dict[str, Any]:
    return {
        "read_only": True,
        "effective": {
            "app_mode": str(settings.app_mode.value),
            "bot_default_starting_cash": settings.bot_default_starting_cash,
            "live_candidate_pipeline_enabled": settings.live_candidate_pipeline_enabled,
        },
        "overrides": None,
        "notes": "Event Edge config is environment-driven; per-strategy overrides are not supported.",
    }


def event_edge_build_dashboard(db: Session, settings: Settings) -> StrategyDashboardBundle:
    sr = build_status_response(db, settings)
    meta = get_strategy_meta(STRATEGY_EVENT_EDGE_V1)
    assert meta is not None
    status = event_edge_status_block(db, settings)

    open_pos = None
    if sr.active_positions:
        p = sr.active_positions[0]
        open_pos = {
            "id": p.id,
            "symbol": p.symbol,
            "strategy": p.strategy,
            "quantity": p.quantity,
            "average_entry_price": p.average_entry_price,
            "unrealized_pnl": p.unrealized_pnl,
            "opened_at": p.opened_at,
        }

    signals: list[dict[str, Any]] = []
    for c in sr.recent_candidates[:25]:
        signals.append(
            {
                "id": c.id,
                "created_at": c.created_at,
                "outcome": c.confirmation_state,
                "setup_family": c.setup_type,
                "direction": c.direction_bias,
                "reason": (c.notes or "")[:240],
                "symbol": c.symbol,
            }
        )

    skipped: list[dict[str, Any]] = []
    for r in sr.recent_rejections[:25]:
        skipped.append(
            {
                "id": r.id,
                "created_at": r.created_at,
                "outcome": "rejected",
                "reason": r.detail or "",
                "rule_codes": r.rule_codes,
            }
        )

    trades: list[dict[str, Any]] = []
    for t in sr.recent_trades[:20]:
        trades.append(
            {
                "id": t.id,
                "created_at": t.created_at,
                "status": t.status,
                "candidate_trade_id": t.candidate_trade_id,
            }
        )

    logs: list[dict[str, Any]] = []
    for d in sr.recent_decisions[:30]:
        logs.append(
            {
                "id": d.id,
                "created_at": d.created_at,
                "bucket": d.bucket,
                "symbol": d.symbol,
                "explanation": (d.explanation or "")[:300],
            }
        )

    analytics_summary = build_analytics_summary(db)
    setups = build_setups_slice(db)
    recommendations = build_recommendation_reads(db, refresh=False)

    return StrategyDashboardBundle(
        status=status,
        daily={
            "realized_pnl": sr.realized_pnl,
            "unrealized_pnl": sr.unrealized_pnl,
            "trade_day": None,
        },
        balances=sr.balances.model_dump(mode="json"),
        open_position=open_pos,
        signals=signals,
        skipped=skipped,
        trades=trades,
        metrics={"analytics_compact": sr.analytics_compact.model_dump(mode="json")},
        logs=logs,
        config=event_edge_get_config(db, settings),
        extensions={
            "runtime_health": build_event_edge_runtime_health(settings),
            "analytics_summary": analytics_summary.model_dump(mode="json"),
            "setups": setups.model_dump(mode="json"),
            "recommendations": [r.model_dump(mode="json") for r in recommendations],
            "full_status": sr.model_dump(mode="json"),
        },
    )
