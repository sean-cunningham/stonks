from pydantic import BaseModel

from app.schemas.analytics import AnalyticsCompactBlock
from app.schemas.account import BalancesRead
from app.schemas.active_position import ActivePositionRead
from app.schemas.approved_trade import ApprovedTradeRead
from app.schemas.candidate_trade import CandidateTradeRead
from app.schemas.event_analysis import EventAnalysisRead
from app.schemas.rejected_trade import RejectedTradeRead
from app.schemas.x_enrichment import XEnrichmentRead


class BotStateRead(BaseModel):
    state: str
    pause_reason: str | None
    cooldown_until: str | None


class FillRead(BaseModel):
    id: int
    active_position_id: int
    side: str
    quantity: int
    price: float
    fee: float
    is_partial: bool
    created_at: str


class StatusResponse(BaseModel):
    bot: BotStateRead
    balances: BalancesRead
    active_positions: list[ActivePositionRead]
    recent_trades: list[ApprovedTradeRead]
    recent_fills: list[FillRead]
    recent_event_analyses: list[EventAnalysisRead]
    recent_x_enrichments: list[XEnrichmentRead]
    recent_candidates: list[CandidateTradeRead]
    recent_rejections: list[RejectedTradeRead]
    latest_account_snapshot_at: str | None
    realized_pnl: float
    unrealized_pnl: float
    analytics_compact: AnalyticsCompactBlock
