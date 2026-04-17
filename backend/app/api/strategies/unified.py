"""Strategy-scoped API: `/strategies/{strategy_id}/...` for all registered bots."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.clock import utc_now
from app.core.config import get_settings
from app.models.active_position import ActivePosition
from app.models.approved_trade import ApprovedTrade
from app.models.candidate_trade import CandidateTrade
from app.models.decision_snapshot import DecisionSnapshot
from app.models.event_analysis import EventAnalysis
from app.models.fill import Fill
from app.models.market_snapshot import MarketSnapshot
from app.models.parameter_experiment_result import ParameterExperimentResult
from app.models.recommendation_item import RecommendationItem
from app.models.rejected_trade import RejectedTrade
from app.models.setup_performance_snapshot import SetupPerformanceSnapshot
from app.models.spy_scalper_candidate_event import SpyScalperCandidateEvent
from app.models.spy_scalper_daily_summary import SpyScalperDailySummary
from app.models.spy_scalper_fill import SpyScalperFill
from app.models.spy_scalper_position import SpyScalperPosition
from app.models.trade_review import TradeReview
from app.models.x_enrichment import XEnrichment
from app.repositories.account_repository import AccountRepository
from app.repositories.bot_state_repository import BotStateRepository
from app.repositories.strategy_bot_state_repository import SPY_SCALPER_SLUG, StrategyBotStateRepository
from app.repositories.spy_scalper_repository import SpyScalperRepository
from app.schemas.strategy_dashboard import (
    StrategyConfigRead,
    StrategyDashboardBundle,
    StrategyDailySummaryRead,
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


@router.get("/{strategy_id}/config", response_model=StrategyConfigRead)
def strategy_get_config(strategy_id: str, db: Session = Depends(get_db)) -> StrategyConfigRead:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        return event_edge_get_config(db, settings)
    return spy_scalper_get_config(db, settings)


class StrategyConfigPayload(BaseModel):
    overrides: dict[str, Any] = Field(default_factory=dict)


@router.put("/{strategy_id}/config", response_model=StrategyConfigRead)
def strategy_put_config(
    strategy_id: str,
    body: StrategyConfigPayload,
    db: Session = Depends(get_db),
) -> StrategyConfigRead:
    _require_strategy(strategy_id)
    settings = get_settings()
    meta = get_strategy_meta(strategy_id)
    assert meta is not None
    if not meta.has_config_put:
        raise HTTPException(status_code=405, detail="config updates not supported for this strategy")
    return spy_scalper_put_config(db, settings, body.overrides)


@router.post("/{strategy_id}/paper-reset", response_model=StrategyStatusBlock)
def strategy_paper_reset(strategy_id: str, db: Session = Depends(get_db)) -> StrategyStatusBlock:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        db.execute(delete(ParameterExperimentResult))
        db.execute(delete(RecommendationItem))
        db.execute(delete(DecisionSnapshot))
        db.execute(delete(TradeReview))
        db.execute(delete(SetupPerformanceSnapshot))
        db.execute(delete(Fill))
        db.execute(delete(XEnrichment))
        db.execute(delete(ActivePosition))
        db.execute(delete(ApprovedTrade))
        db.execute(delete(RejectedTrade))
        db.execute(delete(CandidateTrade))
        db.execute(delete(EventAnalysis))
        db.execute(delete(MarketSnapshot))
        db.commit()
        acc_repo = AccountRepository(db)
        acc = acc_repo.get_primary()
        if acc:
            acc.cash_balance = settings.bot_default_starting_cash
            acc.equity = settings.bot_default_starting_cash
            acc.realized_pnl = 0.0
            acc.unrealized_pnl = 0.0
            acc.updated_at = utc_now()
            db.add(acc)
            db.commit()
        else:
            acc_repo.ensure_primary(settings.bot_default_starting_cash)
        BotStateRepository(db).set_state("stopped", pause_reason=None, cooldown_until=None)
        return event_edge_disable(db, settings)

    db.execute(delete(SpyScalperFill))
    db.execute(delete(SpyScalperPosition))
    db.execute(delete(SpyScalperCandidateEvent))
    db.execute(delete(SpyScalperDailySummary))
    db.commit()
    StrategyBotStateRepository(db).set_state(SPY_SCALPER_SLUG, "stopped", pause_reason=None, cooldown_until=None)
    return spy_scalper_disable(db, settings)


@router.get("/{strategy_id}/metrics/daily", response_model=StrategyDailySummaryRead)
def strategy_metrics_daily(strategy_id: str, db: Session = Depends(get_db)) -> StrategyDailySummaryRead:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        bundle = event_edge_build_dashboard(db, settings)
        return StrategyDailySummaryRead(strategy_id=strategy_id, trade_day=None, metrics=bundle.metrics, details={})
    trade_day = utc_now().date().isoformat()
    spy_repo = SpyScalperRepository(db)
    summary = spy_repo.get_daily_summary(trade_day)
    recent = spy_repo.recent_closed_positions(40)
    return StrategyDailySummaryRead(
        strategy_id=strategy_id,
        trade_day=trade_day,
        metrics=build_daily_metrics(summary, recent),
        details={},
    )


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


@router.get("/{strategy_id}/summary/daily", response_model=StrategyDailySummaryRead)
def strategy_summary_daily(strategy_id: str, db: Session = Depends(get_db)) -> StrategyDailySummaryRead:
    _require_strategy(strategy_id)
    settings = get_settings()
    if strategy_id == STRATEGY_EVENT_EDGE_V1:
        b = event_edge_build_dashboard(db, settings)
        return StrategyDailySummaryRead(strategy_id=strategy_id, trade_day=None, metrics=b.metrics, details=b.daily)
    trade_day = utc_now().date().isoformat()
    spy_repo = SpyScalperRepository(db)
    summary = spy_repo.get_daily_summary(trade_day)
    recent = spy_repo.recent_closed_positions(40)
    return StrategyDailySummaryRead(
        strategy_id=strategy_id,
        trade_day=trade_day,
        metrics=build_daily_metrics(summary, recent),
        details={},
    )
