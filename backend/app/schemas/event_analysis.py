import re
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EventTypeLiteral(StrEnum):
    EARNINGS = "earnings"
    SEC_FILING = "sec_filing"
    MACRO_ANNOUNCEMENT = "macro_announcement"
    HEADLINE = "headline"
    GUIDANCE_CHANGE = "guidance_change"
    TRANSCRIPT = "transcript"
    OTHER = "other"


class DirectionBiasJudgment(StrEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    MIXED = "mixed"
    NONE = "none"


class TimeHorizon(StrEnum):
    MINUTES = "minutes"
    INTRADAY = "intraday"
    MULTI_DAY = "multi_day"


class PricedInRisk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecommendedStrategy(StrEnum):
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    DEBIT_SPREAD = "debit_spread"
    CREDIT_SPREAD = "credit_spread"
    NONE = "none"


class EventAnalysisJudgment(BaseModel):
    """Strict schema for xAI structured output; app-layer validation after API parse."""

    event_type: EventTypeLiteral
    symbol: str = Field(min_length=1, max_length=16)
    materiality_score: int = Field(ge=0, le=100)
    surprise_score: int = Field(ge=0, le=100)
    direction_bias: DirectionBiasJudgment
    confidence_score: int = Field(ge=0, le=100)
    time_horizon: TimeHorizon
    priced_in_risk: PricedInRisk
    narrative_summary: str
    key_evidence_points: list[str]
    tradeability_flag: bool
    recommended_strategy: RecommendedStrategy

    @field_validator("narrative_summary")
    @classmethod
    def two_sentences_max(cls, v: str) -> str:
        text = v.strip()
        if not text:
            raise ValueError("narrative_summary required")
        parts = re.split(r"(?<=[.!?])\s+", text)
        sentences = [p for p in parts if p]
        if len(sentences) > 2:
            raise ValueError("narrative_summary must be at most 2 sentences")
        return text


class EventAnalysisRead(BaseModel):
    id: int
    symbol: str
    event_type: str
    event_source_tier: str
    materiality_score: int
    surprise_score: int
    direction_bias: str
    confidence_score: int
    time_horizon: str
    priced_in_risk: str
    narrative_summary: str
    key_evidence_points: list[str]
    tradeability_flag: bool
    recommended_strategy: str
    validation_ok: bool
    escalation_used: bool
    setup_score: float | None
    reason_codes: list[str] | None
    created_at: str

    model_config = {"from_attributes": False}
