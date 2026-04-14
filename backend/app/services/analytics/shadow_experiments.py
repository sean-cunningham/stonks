"""Offline shadow / what-if parameter comparisons (not executed live)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.parameter_experiment_result import ParameterExperimentResult
from app.models.trade_review import TradeReview
from app.repositories.parameter_experiment_repository import ParameterExperimentRepository

if TYPE_CHECKING:
    from app.core.config import Settings


def run_shadow_experiments_for_review(db: Session, review: TradeReview, *, settings: Settings) -> None:
    repo = ParameterExperimentRepository(db)
    existing = repo.list_for_review(review.id)
    if existing:
        return

    r = review.realized_r_multiple
    pnl = review.realized_pnl_dollars

    row1 = ParameterExperimentResult(
        created_at=utc_now(),
        trade_review_id=review.id,
        experiment_name="wider_initial_stop_20pct",
        parameters_json={"initial_stop_widen_pct": 20},
        outcome_summary=(
            "Counterfactual (offline): a 20% wider initial stop reduces whipsaw exits but increases tail loss; "
            "replay required before any live change."
        ),
        metrics_json={
            "observed_r": r,
            "observed_pnl_usd": pnl,
            "stress_note": "Approximate narrative only — no path replay in V1.",
        },
    )
    repo.create(row1)

    row2 = ParameterExperimentResult(
        created_at=utc_now(),
        trade_review_id=review.id,
        experiment_name="stricter_setup_score_plus5",
        parameters_json={"setup_min_score_delta": 5},
        outcome_summary=(
            "If minimum setup score were +5 points, marginal trades may have been filtered; "
            "validate against full sample, not a single trade."
        ),
        metrics_json={
            "setup_score": review.setup_score,
            "symbol": review.symbol,
        },
    )
    repo.create(row2)

    _ = settings  # reserved for future gated experiments
