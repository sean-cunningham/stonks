from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.api.deps import get_db
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
from app.models.strategy_bot_state import StrategyBotState
from app.models.trade_review import TradeReview
from app.models.x_enrichment import XEnrichment
from app.jobs.scheduler import start_background_jobs, stop_background_jobs
from app.repositories.account_repository import AccountRepository
from app.repositories.bot_state_repository import BotStateRepository
from app.schemas.status import BotStateRead

router = APIRouter(prefix="/bot", tags=["bot"])


def _iso(dt) -> str:
    return dt.isoformat()


@router.get("/state", response_model=BotStateRead)
def bot_state(db: Session = Depends(get_db)) -> BotStateRead:
    row = BotStateRepository(db).get()
    return BotStateRead(
        state=row.state,
        pause_reason=row.pause_reason,
        cooldown_until=_iso(row.cooldown_until) if row.cooldown_until else None,
    )


@router.post("/start", response_model=BotStateRead)
def bot_start(db: Session = Depends(get_db)) -> BotStateRead:
    start_background_jobs(get_settings())
    row = BotStateRepository(db).set_state("running", pause_reason=None)
    return BotStateRead(
        state=row.state,
        pause_reason=row.pause_reason,
        cooldown_until=None,
    )


@router.post("/stop", response_model=BotStateRead)
def bot_stop(db: Session = Depends(get_db)) -> BotStateRead:
    stop_background_jobs()
    row = BotStateRepository(db).set_state("stopped", pause_reason=None)
    return BotStateRead(
        state=row.state,
        pause_reason=row.pause_reason,
        cooldown_until=None,
    )


@router.post("/paper-reset", response_model=BotStateRead)
def paper_reset(db: Session = Depends(get_db)) -> BotStateRead:
    """Destructive global maintenance reset: clears data for all strategies."""
    stop_background_jobs()
    settings = get_settings()
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
    db.execute(delete(SpyScalperFill))
    db.execute(delete(SpyScalperPosition))
    db.execute(delete(SpyScalperCandidateEvent))
    db.execute(delete(SpyScalperDailySummary))
    db.execute(delete(StrategyBotState))
    db.commit()
    acc_repo = AccountRepository(db)
    from app.core.clock import utc_now

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
    bot = BotStateRepository(db).set_state("stopped", pause_reason=None)
    return BotStateRead(
        state=bot.state,
        pause_reason=bot.pause_reason,
        cooldown_until=None,
    )
