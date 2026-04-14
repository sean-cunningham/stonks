from app.services.strategy.setup_scorer import SetupInputs, score_setup


def test_setup_scoring_penalizes_mixed_and_rumor():
    score, reasons = score_setup(
        SetupInputs(
            materiality_score=80,
            confidence_score=80,
            liquidity_ok=True,
            confirmation_ok=True,
            cross_market_ok=True,
            rumor_risk_flag=True,
            event_mixed=True,
        )
    )
    assert score < 80
    assert "event_mixed" in reasons
    assert "rumor_risk_high" in reasons
