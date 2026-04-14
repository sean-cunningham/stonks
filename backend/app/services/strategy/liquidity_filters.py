from dataclasses import dataclass


@dataclass
class LiquidityThresholds:
    max_spread_bps: float = 25.0
    min_volume: float = 100_000.0
    min_strike_count: float = 5.0


def passes_liquidity(
    *,
    spread_bps: float | None,
    volume: float | None,
    strike_count: float | None,
    th: LiquidityThresholds,
) -> tuple[bool, str | None]:
    if spread_bps is None or spread_bps > th.max_spread_bps:
        return False, "spread_too_wide"
    if volume is not None and volume < th.min_volume:
        return False, "volume_too_low"
    if strike_count is not None and strike_count < th.min_strike_count:
        return False, "chain_too_thin"
    return True, None
