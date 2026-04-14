from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JSON = SQLITE_JSON


class XEnrichment(Base):
    __tablename__ = "x_enrichments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    event_analysis_id: Mapped[int | None] = mapped_column(
        ForeignKey("event_analyses.id"),
        nullable=True,
    )
    candidate_trade_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_trades.id"),
        nullable=True,
    )
    provider: Mapped[str] = mapped_column(String(32), default="xai")
    model_name: Mapped[str] = mapped_column(String(64))
    sentiment_bias: Mapped[str] = mapped_column(String(32))
    acceleration_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    rumor_risk_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(Text)
    evidence_points: Mapped[list] = mapped_column(JSON)
    raw_response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
