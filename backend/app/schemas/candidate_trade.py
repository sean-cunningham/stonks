from pydantic import BaseModel


class CandidateTradeRead(BaseModel):
    id: int
    symbol: str
    strategy: str
    candidate_kind: str
    direction_bias: str
    legs: list
    is_event_driven: bool
    setup_type: str | None
    setup_score: float | None
    reason_codes: list[str] | None
    confirmation_state: str | None
    event_id: str | None
    event_analysis_id: int | None
    created_at: str
    notes: str | None
