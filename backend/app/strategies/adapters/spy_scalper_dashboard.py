from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import Settings
from app.jobs.scheduler import ensure_background_jobs_started, maybe_stop_background_jobs
from app.repositories.spy_scalper_repository import SpyScalperRepository
from app.repositories.strategy_bot_state_repository import SPY_SCALPER_SLUG, StrategyBotStateRepository
from app.schemas.strategy_dashboard import StrategyDashboardBundle, StrategyStatusBlock
from app.strategies.registry import STRATEGY_SPY_0DTE_SCALPER, get_strategy_meta
from app.strategies.spy_0dte_scalper.config import effective_config
from app.strategies.spy_0dte_scalper.metrics import build_daily_metrics


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


def _row_to_signal_dict(r) -> dict[str, Any]:
    return {
        "id": r.id,
        "created_at": _iso(r.created_at),
        "trade_day": r.trade_day,
        "outcome": r.outcome,
        "setup_family": r.setup_family,
        "direction": r.direction,
        "base_score": r.base_score,
        "ai_adjustment": r.ai_adjustment,
        "final_score": r.final_score,
        "reason": r.reason,
    }


def spy_scalper_status_block(db: Session, settings: Settings) -> StrategyStatusBlock:
    strat = StrategyBotStateRepository(db)
    row = strat.get_or_create(SPY_SCALPER_SLUG)
    cfg = effective_config(settings, row.config_json)
    spy_repo = SpyScalperRepository(db)
    open_p = spy_repo.get_open_position()
    meta = get_strategy_meta(STRATEGY_SPY_0DTE_SCALPER)
    assert meta is not None
    return StrategyStatusBlock(
        strategy_id=STRATEGY_SPY_0DTE_SCALPER,
        display_name=meta.display_name,
        state=row.state,
        pause_reason=row.pause_reason,
        cooldown_until=_iso(row.cooldown_until),
        paper_only=cfg.paper_only,
        app_mode=str(settings.app_mode.value),
        open_position_id=open_p.id if open_p else None,
    )


def spy_scalper_enable(db: Session, settings: Settings) -> StrategyStatusBlock:
    strat = StrategyBotStateRepository(db)
    strat.set_state(SPY_SCALPER_SLUG, "running", pause_reason=None, cooldown_until=None)
    ensure_background_jobs_started(settings)
    return spy_scalper_status_block(db, settings)


def spy_scalper_disable(db: Session, settings: Settings) -> StrategyStatusBlock:
    strat = StrategyBotStateRepository(db)
    strat.set_state(SPY_SCALPER_SLUG, "stopped", pause_reason=None)
    maybe_stop_background_jobs()
    return spy_scalper_status_block(db, settings)


def spy_scalper_get_config(db: Session, settings: Settings) -> dict[str, Any]:
    strat = StrategyBotStateRepository(db)
    row = strat.get_or_create(SPY_SCALPER_SLUG)
    eff = effective_config(settings, row.config_json)
    return {
        "read_only": False,
        "effective": eff.__dict__,
        "overrides": row.config_json or {},
        "notes": None,
    }


def spy_scalper_put_config(db: Session, settings: Settings, overrides: dict[str, Any]) -> dict[str, Any]:
    strat = StrategyBotStateRepository(db)
    strat.update_config_json(SPY_SCALPER_SLUG, overrides or {})
    row = strat.get_or_create(SPY_SCALPER_SLUG)
    eff = effective_config(settings, row.config_json)
    return {"read_only": False, "effective": eff.__dict__, "overrides": row.config_json or {}, "notes": None}


def spy_scalper_open_position_dict(db: Session) -> dict[str, Any] | None:
    spy_repo = SpyScalperRepository(db)
    p = spy_repo.get_open_position()
    if not p:
        return None
    return {
        "id": p.id,
        "symbol": p.symbol,
        "right": p.right,
        "strike": p.strike,
        "expiry": p.expiry,
        "entry_fill_price": p.entry_fill_price,
        "current_mark": p.current_mark,
        "unrealized_pnl": p.unrealized_pnl,
        "setup_family": p.setup_family,
        "opened_at": _iso(p.opened_at),
        "take_profit_price": p.take_profit_price,
        "stop_price": p.stop_price,
        "max_hold_until": _iso(p.max_hold_until),
    }


def spy_scalper_build_dashboard(db: Session, settings: Settings) -> StrategyDashboardBundle:
    status = spy_scalper_status_block(db, settings)
    trade_day = utc_now().date().isoformat()
    spy_repo = SpyScalperRepository(db)
    summary = spy_repo.get_daily_summary(trade_day)
    recent = spy_repo.recent_closed_positions(40)
    metrics = build_daily_metrics(summary, recent)

    signals = [_row_to_signal_dict(r) for r in spy_repo.recent_candidates(60)]
    skipped = [_row_to_signal_dict(r) for r in spy_repo.recent_skipped_candidates(40)]
    trades: list[dict[str, Any]] = []
    for p in spy_repo.recent_closed_positions(25):
        trades.append(
            {
                "id": p.id,
                "opened_at": _iso(p.opened_at),
                "closed_at": _iso(p.closed_at),
                "setup_family": p.setup_family,
                "right": p.right,
                "strike": p.strike,
                "realized_pnl": p.realized_pnl,
                "close_reason": p.close_reason,
            }
        )

    return StrategyDashboardBundle(
        status=status,
        daily={
            "trade_day": trade_day,
            "net_pnl": float(summary.net_pnl) if summary else 0.0,
            "trades_count": int(summary.trades_count) if summary else 0,
        },
        balances=None,
        open_position=spy_scalper_open_position_dict(db),
        signals=signals,
        skipped=skipped,
        trades=trades,
        metrics=metrics,
        logs=[],
        config=spy_scalper_get_config(db, settings),
        extensions={"summary": {"trade_day": trade_day, "summary": metrics}},
    )
