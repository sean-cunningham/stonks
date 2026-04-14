from dataclasses import dataclass


@dataclass(frozen=True)
class SetupDefinition:
    setup_type: str
    event_required: bool
    anticipatory: bool
    min_score: float


SETUP_LIBRARY: dict[str, SetupDefinition] = {
    "bullish_post_event_confirmation": SetupDefinition(
        setup_type="bullish_post_event_confirmation",
        event_required=True,
        anticipatory=False,
        min_score=65.0,
    ),
    "bearish_post_event_confirmation": SetupDefinition(
        setup_type="bearish_post_event_confirmation",
        event_required=True,
        anticipatory=False,
        min_score=65.0,
    ),
    "anticipatory_macro_event": SetupDefinition(
        setup_type="anticipatory_macro_event",
        event_required=True,
        anticipatory=True,
        min_score=75.0,
    ),
}


def get_setup(name: str) -> SetupDefinition:
    return SETUP_LIBRARY[name]
