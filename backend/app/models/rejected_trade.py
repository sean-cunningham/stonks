from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JSON = SQLITE_JSON


class RejectedTrade(Base):
    __tablename__ = "rejected_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    candidate_trade_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_trades.id"),
        nullable=True,
    )
    event_analysis_id: Mapped[int | None] = mapped_column(
        ForeignKey("event_analyses.id"),
        nullable=True,
    )
    reasons: Mapped[list] = mapped_column(JSON)
    rule_codes: Mapped[list] = mapped_column(JSON)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
