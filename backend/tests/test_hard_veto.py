from app.core.config import Settings
from app.core.enums import RegimeState
from app.models.account import Account
from app.models.candidate_trade import CandidateTrade
from app.models.market_snapshot import MarketSnapshot
from app.services.policy.v1_hard_veto import evaluate_hard_veto
from app.services.strategy.v1_feature_engine import V1FeatureSet
from app.services.strategy.v1_strategy_rules import SetupEvaluation


def _features() -> V1FeatureSet:
    return V1FeatureSet(
        regime=RegimeState.TREND_UP,
        price=500.0,
        vwap=499.0,
        atr5m=1.2,
        rel_volume_5m=1.1,
        opening_range_high=498.0,
        opening_range_low=495.0,
        impulse_size=1.1,
        pullback_depth=0.3,
        overlap_5m_pct=20.0,
        vwap_cross_count_1m=0,
        structure_progression=True,
        levels={"prev_day_high": 505.0, "prev_day_low": 490.0, "premarket_high": 503.0, "premarket_low": 493.0, "opening_range_high": 498.0, "opening_range_low": 495.0, "vwap": 499.0},
        bars_1m=[],
        bars_5m=[],
        bars_15m=[],
    )


def test_hard_veto_stale_quote_and_dte():
    s = Settings()
    c = CandidateTrade(
        id=1,
        symbol="SPY",
        strategy="long_call",
        candidate_kind="x",
        direction_bias="long",
        legs=[{"symbol": "SPY"}],
        is_event_driven=True,
        setup_type="bullish_post_event_confirmation",
        setup_score=90.0,
    )
    snap = MarketSnapshot(
        id=1,
        symbol="SPY",
        spread_bps=2.0,
        volume=900000,
        underlying_price=500.0,
        extra={
            "quote_ts_epoch": 0.0,
            "chain_ts_epoch": 0.0,
            "option_contract": {"dte": 30, "delta": 0.7, "spread_abs": 0.2, "mid": 1.0, "chain_activity_score": 0.2},
        },
    )
    account = Account(id=1, cash_balance=10000, equity=10000, realized_pnl=0, unrealized_pnl=0, currency="USD")
    setup = SetupEvaluation(
        ok=True,
        setup_family="trend_continuation",
        direction="long",
        stop_price=499.0,
        target_price=503.0,
        r_to_target=2.0,
        reason_codes=[],
    )
    out = evaluate_hard_veto(
        now=__import__("datetime").datetime.now(__import__("datetime").UTC),
        candidate=c,
        snapshot=snap,
        event_row=None,
        account=account,
        open_positions=[],
        setup_eval=setup,
        features=_features(),
        settings=s,
        losses_today=0,
        require_confirmation=False,
    )
    assert not out.ok
    assert "QUOTE_STALE" in out.codes
    assert "DTE_OUTSIDE_RANGE" in out.codes
