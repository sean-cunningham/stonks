from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JSON = SQLITE_JSON


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    underlying_price: Mapped[float | None] = mapped_column(nullable=True)
    bid: Mapped[float | None] = mapped_column(nullable=True)
    ask: Mapped[float | None] = mapped_column(nullable=True)
    volume: Mapped[float | None] = mapped_column(nullable=True)
    spread_bps: Mapped[float | None] = mapped_column(nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
