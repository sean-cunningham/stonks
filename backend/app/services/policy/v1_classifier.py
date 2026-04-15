from dataclasses import dataclass

from app.core.enums import DecisionBucket


@dataclass
class ScoreCard:
    setup_quality: int
    regime_fit: int
    liquidity_quality: int
    event_context_safety: int
    execution_quality: int
    historical_support: int


def weighted_score(card: ScoreCard) -> float:
    return (
        card.setup_quality * 1.4
        + card.regime_fit * 1.2
        + card.liquidity_quality * 1.2
        + card.event_context_safety * 1.0
        + card.execution_quality * 1.1
        + card.historical_support * 1.1
    )


def classify_bucket(
    *,
    score: float,
    card: ScoreCard,
    strategy_track: str,
    overnight_required: bool,
    hard_reject: bool,
    recommend_context_uncertainty: bool,
    recommend_outside_auto_risk: bool,
    recommend_event_driven: bool,
    recommend_thin_history: bool,
) -> DecisionBucket:
    if hard_reject:
        return DecisionBucket.REJECT
    if (
        strategy_track == "strategy_a"
        and not overnight_required
        and score >= 30
        and card.setup_quality >= 4
        and card.regime_fit >= 4
        and card.liquidity_quality >= 4
        and card.event_context_safety >= 4
        and card.execution_quality >= 4
        and card.historical_support >= 3
    ):
        return DecisionBucket.AUTO_EXECUTE
    recommend_driver = any(
        [
            recommend_context_uncertainty,
            recommend_outside_auto_risk,
            recommend_event_driven,
            overnight_required,
            recommend_thin_history,
        ]
    )
    if (
        score >= 23
        and card.setup_quality >= 3
        and card.liquidity_quality >= 3
        and card.execution_quality >= 3
        and recommend_driver
    ):
        return DecisionBucket.RECOMMEND_ONLY
    return DecisionBucket.REJECT
