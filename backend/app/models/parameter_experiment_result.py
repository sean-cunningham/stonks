from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JSON = SQLITE_JSON


class ParameterExperimentResult(Base):
    """Offline shadow / what-if outcome linked to a completed trade review."""

    __tablename__ = "parameter_experiment_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    trade_review_id: Mapped[int] = mapped_column(ForeignKey("trade_reviews.id"), index=True)
    experiment_name: Mapped[str] = mapped_column(String(128), index=True)
    parameters_json: Mapped[dict] = mapped_column(JSON)
    outcome_summary: Mapped[str] = mapped_column(Text)
    metrics_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
