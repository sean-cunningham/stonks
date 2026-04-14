from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JSON = SQLITE_JSON


class ApprovedTrade(Base):
    __tablename__ = "approved_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    candidate_trade_id: Mapped[int] = mapped_column(ForeignKey("candidate_trades.id"))
    event_analysis_id: Mapped[int | None] = mapped_column(
        ForeignKey("event_analyses.id"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="pending")
    risk_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    policy_trace: Mapped[dict | None] = mapped_column(JSON, nullable=True)
