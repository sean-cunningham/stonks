from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.repositories.spy_scalper_repository import SpyScalperRepository
from app.repositories.strategy_bot_state_repository import SPY_SCALPER_SLUG, StrategyBotStateRepository
from app.strategies.spy_0dte_scalper.config import effective_config
from app.strategies.spy_0dte_scalper.metrics import build_daily_metrics

router = APIRouter(prefix="/strategies/spy-0dte-scalper", tags=["spy-0dte-scalper"])


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


class ScalperStatusResponse(BaseModel):
    strategy_slug: str = SPY_SCALPER_SLUG
    state: str
    pause_reason: str | None
    cooldown_until: str | None
    paper_only: bool
    open_position_id: int | None = None


@router.get("/status", response_model=ScalperStatusResponse)
def scalper_status(db: Session = Depends(get_db)) -> ScalperStatusResponse:
    settings = get_settings()
    strat = StrategyBotStateRepository(db)
    row = strat.get_or_create(SPY_SCALPER_SLUG)
    cfg = effective_config(settings, row.config_json)
    spy_repo = SpyScalperRepository(db)
    open_p = spy_repo.get_open_position()
    return ScalperStatusResponse(
        state=row.state,
        pause_reason=row.pause_reason,
        cooldown_until=_iso(row.cooldown_until),
        paper_only=cfg.paper_only,
        open_position_id=open_p.id if open_p else None,
    )


@router.post("/enable", response_model=ScalperStatusResponse)
def scalper_enable(db: Session = Depends(get_db)) -> ScalperStatusResponse:
    strat = StrategyBotStateRepository(db)
    row = strat.set_state(SPY_SCALPER_SLUG, "running", pause_reason=None, cooldown_until=None)
    settings = get_settings()
    cfg = effective_config(settings, row.config_json)
    spy_repo = SpyScalperRepository(db)
    open_p = spy_repo.get_open_position()
    return ScalperStatusResponse(
        state=row.state,
        pause_reason=row.pause_reason,
        cooldown_until=_iso(row.cooldown_until),
        paper_only=cfg.paper_only,
        open_position_id=open_p.id if open_p else None,
    )


@router.post("/disable", response_model=ScalperStatusResponse)
def scalper_disable(db: Session = Depends(get_db)) -> ScalperStatusResponse:
    strat = StrategyBotStateRepository(db)
    row = strat.set_state(SPY_SCALPER_SLUG, "stopped", pause_reason=None)
    settings = get_settings()
    cfg = effective_config(settings, row.config_json)
    spy_repo = SpyScalperRepository(db)
    open_p = spy_repo.get_open_position()
    return ScalperStatusResponse(
        state=row.state,
        pause_reason=row.pause_reason,
        cooldown_until=_iso(row.cooldown_until),
        paper_only=cfg.paper_only,
        open_position_id=open_p.id if open_p else None,
    )


class ScalperConfigPayload(BaseModel):
    overrides: dict[str, Any] = Field(default_factory=dict)


@router.get("/config")
def scalper_get_config(db: Session = Depends(get_db)) -> dict[str, Any]:
    settings = get_settings()
    strat = StrategyBotStateRepository(db)
    row = strat.get_or_create(SPY_SCALPER_SLUG)
    eff = effective_config(settings, row.config_json)
    return {"defaults": eff.__dict__, "overrides": row.config_json or {}}


@router.put("/config")
def scalper_put_config(body: ScalperConfigPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    strat = StrategyBotStateRepository(db)
    strat.update_config_json(SPY_SCALPER_SLUG, body.overrides or {})
    row = strat.get_or_create(SPY_SCALPER_SLUG)
    settings = get_settings()
    eff = effective_config(settings, row.config_json)
    return {"effective": eff.__dict__, "overrides": row.config_json or {}}


@router.get("/metrics/daily")
def scalper_metrics_daily(db: Session = Depends(get_db)) -> dict[str, Any]:
    from app.core.clock import utc_now

    trade_day = utc_now().date().isoformat()
    spy_repo = SpyScalperRepository(db)
    summary = spy_repo.get_daily_summary(trade_day)
    recent = spy_repo.recent_closed_positions(40)
    return build_daily_metrics(summary, recent)


@router.get("/signals/recent")
def scalper_signals_recent(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    spy_repo = SpyScalperRepository(db)
    rows = spy_repo.recent_candidates(80)
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
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
        )
    return out


@router.get("/trades/recent")
def scalper_trades_recent(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    spy_repo = SpyScalperRepository(db)
    rows = spy_repo.recent_closed_positions(40)
    out: list[dict[str, Any]] = []
    for p in rows:
        out.append(
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
    return out


@router.get("/logs/recent")
def scalper_logs_recent(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    spy_repo = SpyScalperRepository(db)
    rows = spy_repo.recent_candidates(80)
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
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
        )
    return out


@router.get("/position")
def scalper_position(db: Session = Depends(get_db)) -> dict[str, Any] | None:
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


@router.get("/summary/daily")
def scalper_summary_daily(db: Session = Depends(get_db)) -> dict[str, Any]:
    from app.core.clock import utc_now

    trade_day = utc_now().date().isoformat()
    spy_repo = SpyScalperRepository(db)
    summary = spy_repo.get_daily_summary(trade_day)
    recent = spy_repo.recent_closed_positions(40)
    return {"trade_day": trade_day, "summary": build_daily_metrics(summary, recent)}
