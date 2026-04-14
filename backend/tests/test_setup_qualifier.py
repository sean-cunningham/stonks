from app.services.strategy.setup_qualifier import setup_is_qualified


def test_anticipatory_requires_macro():
    ok, reason = setup_is_qualified(
        setup_type="anticipatory_macro_event",
        setup_score=90,
        event_type="earnings",
        event_mixed=False,
    )
    assert not ok
    assert reason == "anticipatory_requires_macro_event"
