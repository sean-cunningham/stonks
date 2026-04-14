from app.schemas.event_analysis import DirectionBiasJudgment


def price_confirms_bias(
    *,
    bullish_candidate: bool,
    bid: float | None,
    ask: float | None,
    last: float | None,
    ref_price: float | None,
) -> tuple[bool, str | None]:
    """Real-time confirmation: directional trades need price not contradicting bias."""
    mid = None
    if bid and ask and bid > 0 and ask > 0:
        mid = (bid + ask) / 2
    px = last or mid
    if px is None or ref_price is None or ref_price <= 0:
        return False, "missing_quote"
    drift = (px - ref_price) / ref_price
    if bullish_candidate and drift < -0.001:
        return False, "price_not_bullish"
    if not bullish_candidate and drift > 0.001:
        return False, "price_not_bearish"
    return True, None


def ai_bias_matches_direction(
    ai_bias: DirectionBiasJudgment | str,
    *,
    bullish_trade: bool,
) -> bool:
    if isinstance(ai_bias, str):
        bias = ai_bias
    else:
        bias = ai_bias.value
    if bullish_trade:
        return bias in ("bullish", "mixed")
    return bias in ("bearish", "mixed")
