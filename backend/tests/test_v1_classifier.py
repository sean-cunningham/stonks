from app.core.enums import DecisionBucket
from app.services.policy.v1_classifier import ScoreCard, classify_bucket, weighted_score


def test_auto_execute_threshold():
    card = ScoreCard(
        setup_quality=5,
        regime_fit=5,
        liquidity_quality=5,
        event_context_safety=5,
        execution_quality=5,
        historical_support=4,
    )
    score = weighted_score(card)
    bucket = classify_bucket(
        score=score,
        card=card,
        strategy_track="strategy_a",
        overnight_required=False,
        hard_reject=False,
        recommend_context_uncertainty=False,
        recommend_outside_auto_risk=False,
        recommend_event_driven=False,
        recommend_thin_history=False,
    )
    assert score >= 30
    assert bucket == DecisionBucket.AUTO_EXECUTE


def test_recommend_only_threshold():
    card = ScoreCard(
        setup_quality=4,
        regime_fit=3,
        liquidity_quality=4,
        event_context_safety=3,
        execution_quality=4,
        historical_support=3,
    )
    score = weighted_score(card)
    bucket = classify_bucket(
        score=score,
        card=card,
        strategy_track="strategy_b",
        overnight_required=False,
        hard_reject=False,
        recommend_context_uncertainty=True,
        recommend_outside_auto_risk=False,
        recommend_event_driven=False,
        recommend_thin_history=False,
    )
    assert score >= 23
    assert bucket == DecisionBucket.RECOMMEND_ONLY
