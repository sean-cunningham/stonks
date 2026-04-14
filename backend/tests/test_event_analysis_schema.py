import pytest
from pydantic import ValidationError

from app.schemas.event_analysis import EventAnalysisJudgment, EventTypeLiteral


def test_valid_judgment():
    j = EventAnalysisJudgment(
        event_type=EventTypeLiteral.EARNINGS,
        symbol="SPY",
        materiality_score=50,
        surprise_score=40,
        direction_bias="bullish",
        confidence_score=60,
        time_horizon="intraday",
        priced_in_risk="low",
        narrative_summary="Beat on EPS. Revenue was in line.",
        key_evidence_points=["eps beat"],
        tradeability_flag=True,
        recommended_strategy="debit_spread",
    )
    assert j.symbol == "SPY"


def test_narrative_too_many_sentences():
    with pytest.raises(ValidationError):
        EventAnalysisJudgment(
            event_type="headline",
            symbol="AAPL",
            materiality_score=1,
            surprise_score=1,
            direction_bias="none",
            confidence_score=1,
            time_horizon="minutes",
            priced_in_risk="high",
            narrative_summary="First sentence. Second sentence. Third bad.",
            key_evidence_points=[],
            tradeability_flag=False,
            recommended_strategy="none",
        )


def test_score_out_of_range():
    with pytest.raises(ValidationError):
        EventAnalysisJudgment(
            event_type="other",
            symbol="QQQ",
            materiality_score=101,
            surprise_score=0,
            direction_bias="mixed",
            confidence_score=0,
            time_horizon="multi_day",
            priced_in_risk="medium",
            narrative_summary="Ok.",
            key_evidence_points=[],
            tradeability_flag=False,
            recommended_strategy="none",
        )
