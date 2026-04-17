"""Strategy-scoped API: `/strategies/{strategy_id}/...` for all registered bots."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.clock import utc_now
from app.core.config import get_settings
from app.repositories.spy_scalper_repository import SpyScalperRepository
from app.schemas.strategy_dashboard import (
    StrategyDashboardBundle,
    StrategyListItem,
    StrategyStatusBlock,
)
from app.strategies.adapters.event_edge_dashboard import (
    event_edge_build_dashboard,
    event_edge_disable,
    event_edge_enable,
    event_edge_get_config,
    event_edge_status_block,
)
from app.strategies.adapters.spy_scalper_dashboard import (
    spy_scalper_build_dashboard,
    spy_scalper_disable,
    spy_scalper_enable,
    spy_scalper_get_config,
    spy_scalper_open_position_dict,
    spy_scalper_put_config,
    spy_scalper_status_block,
)
from app.strategies.registry import (
    STRATEGY_EVENT_EDGE_V1,
    STRATEGY_SPY_0DTE_SCALPER,
    all_strategies,
    get_strategy_meta,
    is_known_strategy_id,
)
from app.strategies.spy_0dte_scalper.metrics import build_daily_metrics

router = APIRouter(prefix="/strategies", tags=["strategies"])


def _require_strategy(strategy_id: str) -> None:
    if not is_known_strategy_id(strategy_id):
        raise HTTPException(status_code=404, detail=f"unknown strategy_id: {strategy_id}")


@router.get("", response_model=list[StrategyListItem])
def list_strategies() -> list[StrategyListItem]:
    return [
        StrategyListItem(
            strategy_id=m.strategy_id,
            display_name=m.display_name,
            description=m.description,
            has_config_put=m.has_config_put,
            has_skipped_feed=m.has_skipped_feed,
        )
        for m in all_strategies()
    ]


@router.get("/{strategy_id}/dashboard", response_model=StrategyDashboardBundle)
def strategy_dashboard(strategy_id: str, db: Session = Depends(get_db)) -> StrategyDashboardBundle:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        return event_edge_build_dashboard(db, settings)
    return spy_scalper_build_dashboard(db, settings)


@router.get("/{strategy_id}/status", response_model=StrategyStatusBlock)
def strategy_status(strategy_id: str, db: Session = Depends(get_db)) -> StrategyStatusBlock:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        return event_edge_status_block(db, settings)
    return spy_scalper_status_block(db, settings)


@router.post("/{strategy_id}/enable", response_model=StrategyStatusBlock)
def strategy_enable(strategy_id: str, db: Session = Depends(get_db)) -> StrategyStatusBlock:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        return event_edge_enable(db, settings)
    return spy_scalper_enable(db, settings)


@router.post("/{strategy_id}/disable", response_model=StrategyStatusBlock)
def strategy_disable(strategy_id: str, db: Session = Depends(get_db)) -> StrategyStatusBlock:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        return event_edge_disable(db, settings)
    return spy_scalper_disable(db, settings)


@router.get("/{strategy_id}/config")
def strategy_get_config(strategy_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        return event_edge_get_config(db, settings)
    return spy_scalper_get_config(db, settings)


class StrategyConfigPayload(BaseModel):
    overrides: dict[str, Any] = Field(default_factory=dict)


@router.put("/{strategy_id}/config")
def strategy_put_config(
    strategy_id: str,
    body: StrategyConfigPayload,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _require_strategy(strategy_id)
    settings = get_settings()
    meta = get_strategy_meta(strategy_id)
    assert meta is not None
    if not meta.has_config_put:
        raise HTTPException(status_code=405, detail="config updates not supported for this strategy")
    return spy_scalper_put_config(db, settings, body.overrides)


@router.get("/{strategy_id}/metrics/daily")
def strategy_metrics_daily(strategy_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        bundle = event_edge_build_dashboard(db, settings)
        return bundle.metrics
    trade_day = utc_now().date().isoformat()
    spy_repo = SpyScalperRepository(db)
    summary = spy_repo.get_daily_summary(trade_day)
    recent = spy_repo.recent_closed_positions(40)
    return build_daily_metrics(summary, recent)


@router.get("/{strategy_id}/signals/recent")
def strategy_signals_recent(strategy_id: str, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        return event_edge_build_dashboard(db, settings).signals
    return spy_scalper_build_dashboard(db, settings).signals


@router.get("/{strategy_id}/signals/skipped")
def strategy_signals_skipped(strategy_id: str, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        return event_edge_build_dashboard(db, settings).skipped
    return spy_scalper_build_dashboard(db, settings).skipped


@router.get("/{strategy_id}/trades/recent")
def strategy_trades_recent(strategy_id: str, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        return event_edge_build_dashboard(db, settings).trades
    return spy_scalper_build_dashboard(db, settings).trades


@router.get("/{strategy_id}/logs/recent")
def strategy_logs_recent(strategy_id: str, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        return event_edge_build_dashboard(db, settings).logs
    return spy_scalper_build_dashboard(db, settings).logs


@router.get("/{strategy_id}/position")
def strategy_position(strategy_id: str, db: Session = Depends(get_db)) -> dict[str, Any] | None:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        b = event_edge_build_dashboard(db, settings)
        return b.open_position
    return spy_scalper_open_position_dict(db)


@router.get("/{strategy_id}/summary/daily")
def strategy_summary_daily(strategy_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        b = event_edge_build_dashboard(db, settings)
        return {"trade_day": None, "summary": b.metrics, "daily": b.daily}
    trade_day = utc_now().date().isoformat()
    spy_repo = SpyScalperRepository(db)
    summary = spy_repo.get_daily_summary(trade_day)
    recent = spy_repo.recent_closed_positions(40)
    return {"trade_day": trade_day, "summary": build_daily_metrics(summary, recent)}
