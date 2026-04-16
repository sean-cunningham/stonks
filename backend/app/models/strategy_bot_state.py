from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JSON = SQLITE_JSON


class StrategyBotState(Base):
    __tablename__ = "strategy_bot_states"

    strategy_slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    state: Mapped[str] = mapped_column(String(32), default="stopped")
    pause_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cooldown_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scalper_state_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
