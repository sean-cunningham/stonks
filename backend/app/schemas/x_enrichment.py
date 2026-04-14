from pydantic import BaseModel


class XEnrichmentRead(BaseModel):
    id: int
    symbol: str
    provider: str
    model_name: str
    sentiment_bias: str
    acceleration_flag: bool
    rumor_risk_flag: bool
    confidence_score: int
    summary: str
    evidence_points: list[str]
    event_analysis_id: int | None
    candidate_trade_id: int | None
    created_at: str
