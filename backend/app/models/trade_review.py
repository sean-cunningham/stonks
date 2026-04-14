from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JSON = SQLITE_JSON


class TradeReview(Base):
    """Post-trade journal row: analytics-only; does not alter live strategy."""

    __tablename__ = "trade_reviews"
    __table_args__ = (UniqueConstraint("approved_trade_id", name="uq_trade_reviews_approved_trade_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    approved_trade_id: Mapped[int] = mapped_column(ForeignKey("approved_trades.id"), index=True)
    candidate_trade_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_trades.id"),
        nullable=True,
    )
    active_position_id: Mapped[int | None] = mapped_column(
        ForeignKey("active_positions.id"),
        nullable=True,
    )
    event_analysis_id: Mapped[int | None] = mapped_column(
        ForeignKey("event_analyses.id"),
        nullable=True,
    )

    symbol: Mapped[str] = mapped_column(String(16), index=True)
    setup_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    setup_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confirmation_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    event_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trade_family: Mapped[str] = mapped_column(String(32), default="confirmed", index=True)

    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    realized_pnl_dollars: Mapped[float] = mapped_column(Float)
    realized_r_multiple: Mapped[float | None] = mapped_column(Float, nullable=True)
    mfe_dollars: Mapped[float | None] = mapped_column(Float, nullable=True)
    mae_dollars: Mapped[float | None] = mapped_column(Float, nullable=True)

    holding_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hit_plus_1r: Mapped[bool] = mapped_column(Boolean, default=False)
    hit_plus_1_5r: Mapped[bool] = mapped_column(Boolean, default=False)
    hit_plus_2r: Mapped[bool] = mapped_column(Boolean, default=False)

    rule_adherence_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    had_x_enrichment: Mapped[bool] = mapped_column(Boolean, default=False)
    had_thenewsapi_supplement: Mapped[bool] = mapped_column(Boolean, default=False)
    reason_codes_snapshot: Mapped[list | None] = mapped_column(JSON, nullable=True)
    policy_trace_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    exit_quality_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    exit_quality_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    journaling_version: Mapped[int] = mapped_column(Integer, default=1)
