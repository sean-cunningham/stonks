def index_cross_market_confirmation(
    *,
    symbol: str,
    bullish: bool,
    es_change_pct: float | None,
    nq_change_pct: float | None,
    vix_change_pct: float | None,
    yield_change_bps: float | None,
    breadth_ratio: float | None,
) -> bool:
    if symbol not in {"SPY", "QQQ", "IWM"}:
        return True
    checks = 0
    good = 0
    if es_change_pct is not None:
        checks += 1
        good += int(es_change_pct > 0 if bullish else es_change_pct < 0)
    if nq_change_pct is not None:
        checks += 1
        good += int(nq_change_pct > 0 if bullish else nq_change_pct < 0)
    if vix_change_pct is not None:
        checks += 1
        good += int(vix_change_pct < 0 if bullish else vix_change_pct > 0)
    if yield_change_bps is not None:
        checks += 1
        good += int(yield_change_bps <= 0 if bullish else yield_change_bps >= 0)
    if breadth_ratio is not None:
        checks += 1
        good += int(breadth_ratio >= 1.0 if bullish else breadth_ratio <= 1.0)
    if checks == 0:
        return False
    return good / checks >= 0.6
