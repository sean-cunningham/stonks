from pydantic import BaseModel


class ApprovedTradeRead(BaseModel):
    id: int
    candidate_trade_id: int
    event_analysis_id: int | None
    status: str
    created_at: str
    risk_snapshot: dict | None
    policy_trace: dict | None
