from app.services.strategy.cross_market_confirmation import index_cross_market_confirmation


def test_index_cross_market_confirmation_bullish():
    assert index_cross_market_confirmation(
        symbol="SPY",
        bullish=True,
        es_change_pct=0.5,
        nq_change_pct=0.4,
        vix_change_pct=-2.0,
        yield_change_bps=-1.0,
        breadth_ratio=1.3,
    )
