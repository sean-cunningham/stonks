from app.services.strategy.regime_detector import Regime


def continuation_allows(
    regime: Regime,
    *,
    bullish: bool,
) -> bool:
    if bullish:
        return regime == Regime.TREND_UP
    return regime == Regime.TREND_DOWN


def post_event_allows(
    regime: Regime,
    *,
    bullish: bool,
) -> bool:
    """Post-event: require non-conflicting regime (not strongly opposite)."""
    if bullish:
        return regime != Regime.TREND_DOWN
    return regime != Regime.TREND_UP
