from datetime import UTC, datetime

from app.core.config import Settings
from app.models.market_snapshot import MarketSnapshot
from app.services.strategy.candidate_generator import maybe_build_candidate
from app.services.strategy.liquidity_filters import LiquidityThresholds


def _snap(
    *,
    sym: str = "SPY",
    spread: float = 10.0,
    vol: float = 500_000,
    strikes: float = 20,
    price: float = 500.0,
) -> MarketSnapshot:
    return MarketSnapshot(
        symbol=sym,
        created_at=datetime.now(UTC),
        underlying_price=price,
        bid=price - 0.05,
        ask=price + 0.05,
        volume=vol,
        spread_bps=spread,
        extra={"chain_liquidity": {"strike_count": strikes}},
    )


def test_rejects_bad_symbol():
    s = _snap(sym="ZZZZ")
    spec, reason = maybe_build_candidate(
        s,
        settings=Settings(),
        event_type="headline",
        event_id="e-1",
        direction_bias="bullish",
        materiality_score=70,
        confidence_score=60,
        event_mixed=False,
    )
    assert spec is None
    assert reason == "symbol_not_watched"


def test_bullish_post_event_setup_generated():
    s = _snap(price=525)
    spec, reason = maybe_build_candidate(
        s,
        settings=Settings(),
        event_type="earnings",
        event_id="earn-1",
        direction_bias="bullish",
        materiality_score=80,
        confidence_score=80,
        event_mixed=False,
        liquidity=LiquidityThresholds(max_spread_bps=100, min_volume=1, min_strike_count=1),
    )
    assert reason is None
    assert spec is not None
    assert spec.setup_type == "bullish_post_event_confirmation"
