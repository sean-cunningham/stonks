from app.services.market_data.quote_cache import QuoteCache, QuoteTick


def test_spread_bps():
    c = QuoteCache()
    c.update(QuoteTick(symbol="SPY", bid=100.0, ask=100.10))
    bps = c.spread_bps("SPY")
    assert bps is not None
    assert 9 < bps < 11
