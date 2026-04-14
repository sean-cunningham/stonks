from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JSON = SQLITE_JSON


class SetupPerformanceSnapshot(Base):
    """Cached rollup of analytics for a dimension (e.g. per setup_type)."""

    __tablename__ = "setup_performance_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    dimension_type: Mapped[str] = mapped_column(String(32), index=True)
    dimension_key: Mapped[str] = mapped_column(String(128), index=True)
    metrics_json: Mapped[dict] = mapped_column(JSON)
    trade_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
