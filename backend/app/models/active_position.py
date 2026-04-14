from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JSON = SQLITE_JSON


class ActivePosition(Base):
    __tablename__ = "active_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    approved_trade_id: Mapped[int] = mapped_column(ForeignKey("approved_trades.id"))
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    strategy: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    legs: Mapped[list] = mapped_column(JSON)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    average_entry_price: Mapped[float] = mapped_column(Float)
    market_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unrealized_pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    initial_stop_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    emergency_premium_stop_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_trailing_stop: Mapped[float | None] = mapped_column(Float, nullable=True)
    breakeven_armed: Mapped[bool] = mapped_column(default=False)
    partial_exit_taken: Mapped[bool] = mapped_column(default=False)
    partial_exit_qty: Mapped[int] = mapped_column(Integer, default=0)
    thesis_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    high_water_mark_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    low_water_mark_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    reached_1r: Mapped[bool] = mapped_column(Boolean, default=False)
    reached_1_5r: Mapped[bool] = mapped_column(Boolean, default=False)
    reached_2r: Mapped[bool] = mapped_column(Boolean, default=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
