from app.services.analytics.exit_classifier import classify_exit


def test_exit_classifier_thesis():
    label, _ = classify_exit(
        realized_pnl_dollars=-10.0,
        mfe_dollars=5.0,
        mae_dollars=20.0,
        exit_reason="thesis_expired",
        hit_plus_1r=False,
        hit_plus_2r=False,
    )
    assert label == "thesis_expired_exit"


def test_exit_classifier_adverse_stop():
    label, expl = classify_exit(
        realized_pnl_dollars=-40.0,
        mfe_dollars=2.0,
        mae_dollars=50.0,
        exit_reason="trailing_stop_hit",
        hit_plus_1r=False,
        hit_plus_2r=False,
    )
    assert label == "adverse_stop_exit"
    assert "limited favorable" in expl


def test_exit_classifier_gave_back():
    label, _ = classify_exit(
        realized_pnl_dollars=30.0,
        mfe_dollars=200.0,
        mae_dollars=10.0,
        exit_reason="trailing_stop_hit",
        hit_plus_1r=True,
        hit_plus_2r=True,
    )
    assert label == "gave_back_winner"
