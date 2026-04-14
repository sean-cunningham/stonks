from pydantic import BaseModel


class RejectedTradeRead(BaseModel):
    id: int
    candidate_trade_id: int | None
    event_analysis_id: int | None
    reasons: list
    rule_codes: list
    detail: str | None
    created_at: str
