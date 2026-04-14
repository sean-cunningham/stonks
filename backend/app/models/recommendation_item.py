from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JSON = SQLITE_JSON


class RecommendationItem(Base):
    """Human-review suggestions only; execution layer must not auto-apply."""

    __tablename__ = "recommendation_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(32), default="suggested_for_review", index=True)
    title: Mapped[str] = mapped_column(String(256))
    evidence_summary: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    affected_scope: Mapped[dict] = mapped_column(JSON)
    suggested_parameter_delta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    trade_review_id: Mapped[int | None] = mapped_column(
        ForeignKey("trade_reviews.id"),
        nullable=True,
    )
