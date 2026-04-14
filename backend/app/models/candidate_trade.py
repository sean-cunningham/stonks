from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JSON = SQLITE_JSON


class CandidateTrade(Base):
    __tablename__ = "candidate_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    market_snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("market_snapshots.id"),
        nullable=True,
    )
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    strategy: Mapped[str] = mapped_column(String(32))
    candidate_kind: Mapped[str] = mapped_column(String(64))
    direction_bias: Mapped[str] = mapped_column(String(32))
    legs: Mapped[list] = mapped_column(JSON)
    is_event_driven: Mapped[bool] = mapped_column(Boolean, default=False)
    setup_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    setup_score: Mapped[float | None] = mapped_column(nullable=True)
    reason_codes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confirmation_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    event_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_analysis_id: Mapped[int | None] = mapped_column(
        ForeignKey("event_analyses.id"),
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
