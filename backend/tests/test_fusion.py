from datetime import UTC, datetime

from app.models.candidate_trade import CandidateTrade
from app.models.market_snapshot import MarketSnapshot
from app.services.policy.fusion_engine import evaluate_fusion


def _cand(**kw) -> CandidateTrade:
    defaults = dict(
        id=1,
        created_at=datetime.now(UTC),
        market_snapshot_id=1,
        symbol="SPY",
        strategy="debit_spread",
        setup_type="bullish_post_event_confirmation",
        setup_score=82.0,
        reason_codes=["liquidity_ok"],
        confirmation_state="confirmed",
        event_id="e-1",
        candidate_kind="bullish_post_event_confirmation",
        direction_bias="long",
        legs=[],
        is_event_driven=False,
        event_analysis_id=None,
        metadata_json=None,
        notes=None,
    )
    defaults.update(kw)
    return CandidateTrade(**defaults)


def _snap() -> MarketSnapshot:
    return MarketSnapshot(
        id=1,
        symbol="SPY",
        created_at=datetime.now(UTC),
        underlying_price=500.0,
        bid=499.9,
        ask=500.1,
        volume=1e6,
        spread_bps=5.0,
        extra={"chain_liquidity": {"strike_count": 30}},
    )


def test_fusion_happy_path():
    c = _cand()
    s = _snap()
    r = evaluate_fusion(candidate=c, snapshot=s, event_row=None, open_positions=[])
    assert r.ok
