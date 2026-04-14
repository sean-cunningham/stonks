from enum import StrEnum


class Regime(StrEnum):
    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    RANGE = "range"
    UNKNOWN = "unknown"


def detect_regime(
    prices: list[float],
    *,
    short_window: int = 3,
    long_window: int = 8,
) -> Regime:
    """Simple momentum/regime from closing prices (oldest first)."""
    clean = [p for p in prices if p and p > 0]
    if len(clean) < max(short_window, long_window):
        return Regime.UNKNOWN
    short = sum(clean[-short_window:]) / short_window
    long = sum(clean[-long_window:]) / long_window
    if short > long * 1.002:
        return Regime.TREND_UP
    if short < long * 0.998:
        return Regime.TREND_DOWN
    return Regime.RANGE
