from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JSON = SQLITE_JSON


class EventAnalysis(Base):
    __tablename__ = "event_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    normalized_event_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_source_tier: Mapped[str] = mapped_column(String(32), default="official")
    event_type: Mapped[str] = mapped_column(String(64))
    materiality_score: Mapped[int] = mapped_column(Integer)
    surprise_score: Mapped[int] = mapped_column(Integer)
    direction_bias: Mapped[str] = mapped_column(String(32))
    confidence_score: Mapped[int] = mapped_column(Integer)
    time_horizon: Mapped[str] = mapped_column(String(32))
    priced_in_risk: Mapped[str] = mapped_column(String(32))
    narrative_summary: Mapped[str] = mapped_column(Text)
    key_evidence_points: Mapped[list] = mapped_column(JSON)
    tradeability_flag: Mapped[bool] = mapped_column(Boolean)
    recommended_strategy: Mapped[str] = mapped_column(String(32))
    raw_response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    escalation_used: Mapped[bool] = mapped_column(Boolean, default=False)
    setup_score: Mapped[float | None] = mapped_column(nullable=True)
    reason_codes: Mapped[list | None] = mapped_column(JSON, nullable=True)
