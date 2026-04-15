from pydantic import BaseModel


class DecisionSnapshotRead(BaseModel):
    id: int
    created_at: str
    symbol: str
    candidate_trade_id: int | None
    approved_trade_id: int | None
    bucket: str
    strategy_track: str
    hard_vetoes: list[str]
    hard_veto_codes: list[str]
    scores: dict | None
    weighted_score: float | None
    explanation: str | None
