from app.services.strategy.setup_registry import get_setup


def setup_is_qualified(
    *,
    setup_type: str,
    setup_score: float,
    event_type: str,
    event_mixed: bool,
) -> tuple[bool, str | None]:
    setup = get_setup(setup_type)
    if event_mixed:
        return False, "event_mixed"
    if setup_score < setup.min_score:
        return False, "setup_score_below_threshold"
    if setup_type == "anticipatory_macro_event" and event_type != "macro_announcement":
        return False, "anticipatory_requires_macro_event"
    return True, None
