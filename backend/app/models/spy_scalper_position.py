from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SpyScalperPosition(Base):
    __tablename__ = "spy_scalper_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), default="SPY")
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    right: Mapped[str] = mapped_column(String(4))
    strike: Mapped[float] = mapped_column(Float)
    expiry: Mapped[str] = mapped_column(String(16))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    entry_mid: Mapped[float] = mapped_column(Float)
    entry_fill_price: Mapped[float] = mapped_column(Float)
    exit_fill_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_mark: Mapped[float | None] = mapped_column(Float, nullable=True)
    unrealized_pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    setup_family: Mapped[str | None] = mapped_column(String(64), nullable=True)
    high_water_mark: Mapped[float | None] = mapped_column(Float, nullable=True)
    low_water_mark: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_hold_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fast_fail_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    close_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
