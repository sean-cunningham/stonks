from dataclasses import dataclass


@dataclass
class LevelContext:
    vwap: float | None = None
    prior_day_high: float | None = None
    prior_day_low: float | None = None
    premarket_high: float | None = None
    premarket_low: float | None = None
    opening_range_high: float | None = None
    opening_range_low: float | None = None
    round_number: float | None = None
    major_strike: float | None = None


def confirm_direction(
    *,
    bullish: bool,
    price: float | None,
    levels: LevelContext,
) -> bool:
    if price is None:
        return False
    refs = [
        levels.vwap,
        levels.prior_day_high if bullish else levels.prior_day_low,
        levels.opening_range_high if bullish else levels.opening_range_low,
        levels.round_number,
        levels.major_strike,
    ]
    refs = [r for r in refs if r is not None]
    if not refs:
        return False
    if bullish:
        return price >= max(refs) * 0.997
    return price <= min(refs) * 1.003
