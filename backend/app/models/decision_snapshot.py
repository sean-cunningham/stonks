from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JSON = SQLITE_JSON


class DecisionSnapshot(Base):
    __tablename__ = "decision_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    candidate_trade_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_trades.id"),
        nullable=True,
    )
    event_analysis_id: Mapped[int | None] = mapped_column(
        ForeignKey("event_analyses.id"),
        nullable=True,
    )
    approved_trade_id: Mapped[int | None] = mapped_column(
        ForeignKey("approved_trades.id"),
        nullable=True,
    )
    bucket: Mapped[str] = mapped_column(String(32), index=True)
    strategy_track: Mapped[str] = mapped_column(String(32), index=True)
    hard_vetoes: Mapped[list] = mapped_column(JSON)
    hard_veto_codes: Mapped[list] = mapped_column(JSON)
    scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    weighted_score: Mapped[float | None] = mapped_column(nullable=True)
    market_state_json: Mapped[dict] = mapped_column(JSON)
    option_state_json: Mapped[dict] = mapped_column(JSON)
    risk_state_json: Mapped[dict] = mapped_column(JSON)
    context_state_json: Mapped[dict] = mapped_column(JSON)
    historical_state_json: Mapped[dict] = mapped_column(JSON)
    order_instruction_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
