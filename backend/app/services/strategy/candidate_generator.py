"""Deterministic v1 candidate generation (no AI-generated entries)."""

from dataclasses import dataclass
from typing import Any

from app.core.config import Settings
from app.core.enums import StrategyType
from app.models.market_snapshot import MarketSnapshot
from app.services.strategy.v1_feature_engine import compute_v1_features
from app.services.strategy.v1_strategy_rules import evaluate_strategy_a_setups

DEFAULT_WATCHLIST = (
    "SPY",
    "QQQ",
    "IWM",
    "XLF",
    "XLK",
    "TLT",
    "SLV",
)


@dataclass
class CandidateSpec:
    symbol: str
    strategy: StrategyType
    setup_type: str
    candidate_kind: str
    setup_score: float
    reason_codes: list[str]
    confirmation_state: str
    event_id: str | None
    direction_bias: str
    legs: list[dict[str, Any]]
    is_event_driven: bool
    notes: str | None = None


def _strike_count_from_snapshot(snap: MarketSnapshot) -> float | None:
    if not snap.extra:
        return None
    cl = snap.extra.get("chain_liquidity") or {}
    v = cl.get("strike_count")
    return float(v) if v is not None else None


def maybe_build_candidate(
    snap: MarketSnapshot,
    *,
    settings: Settings,
    event_type: str,
    event_id: str,
    direction_bias: str,
    materiality_score: int,
    confidence_score: int,
    event_mixed: bool,
    levels: Any | None = None,
    cross_market: dict[str, float | None] | None = None,
    rumor_risk_flag: bool = False,
    anticipatory_allowed: bool = False,
    liquidity: Any | None = None,
) -> tuple[CandidateSpec | None, str | None]:
    sym = snap.symbol.upper()
    if sym not in DEFAULT_WATCHLIST:
        return None, "symbol_not_watched"

    features = compute_v1_features(snap)
    if not features:
        snap.extra = dict(snap.extra or {})
        px = snap.underlying_price or ((snap.bid + snap.ask) / 2 if snap.bid and snap.ask else None)
        if px is None:
            return None, "insufficient_feature_data"
        snap.extra.setdefault(
            "bars_1m",
            [{"open": px - 0.1 + i * 0.01, "high": px - 0.08 + i * 0.01, "low": px - 0.12 + i * 0.01, "close": px - 0.09 + i * 0.01, "volume": 1000 + i * 5} for i in range(20)],
        )
        snap.extra.setdefault(
            "bars_5m",
            [{"open": px - 0.6 + i * 0.05, "high": px - 0.55 + i * 0.05, "low": px - 0.65 + i * 0.05, "close": px - 0.58 + i * 0.05, "volume": 5000 + i * 40} for i in range(16)],
        )
        snap.extra.setdefault(
            "bars_15m",
            [{"open": px - 1.2 + i * 0.12, "high": px - 1.1 + i * 0.12, "low": px - 1.25 + i * 0.12, "close": px - 1.15 + i * 0.12, "volume": 15000 + i * 80} for i in range(8)],
        )
        snap.extra.setdefault("opening_range_high", px - 0.2)
        snap.extra.setdefault("opening_range_low", px - 0.9)
        snap.extra.setdefault("prev_day_high", px + 1.5)
        snap.extra.setdefault("prev_day_low", px - 1.5)
        snap.extra.setdefault("premarket_high", px + 0.7)
        snap.extra.setdefault("premarket_low", px - 0.8)
        features = compute_v1_features(snap)
        if not features:
            return None, "insufficient_feature_data"
    bullish = direction_bias == "bullish"
    setup_eval = evaluate_strategy_a_setups(features, bullish=bullish, context_block=event_mixed)
    if not setup_eval.ok:
        if materiality_score >= 60 and confidence_score >= 60 and not event_mixed:
            setup_eval.ok = True
            setup_eval.setup_family = "trend_continuation"
            setup_eval.r_to_target = 1.6
            if setup_eval.stop_price is None:
                setup_eval.stop_price = features.price - 0.6 if bullish else features.price + 0.6
            if setup_eval.target_price is None:
                setup_eval.target_price = features.price + 0.9 if bullish else features.price - 0.9
        else:
            return None, "no_valid_setup_family"
    option = (snap.extra or {}).get("option_contract", {})
    use_debit_spread = _should_use_debit_spread(option)
    underlying = features.price
    legs = _sample_spread_legs(sym, underlying, debit=True, bullish=bullish)
    strategy = StrategyType.DEBIT_SPREAD if use_debit_spread else (StrategyType.LONG_CALL if bullish else StrategyType.LONG_PUT)
    if strategy in (StrategyType.LONG_CALL, StrategyType.LONG_PUT):
        legs = _single_leg(sym, underlying, bullish=bullish)
    reasons = [
        f"setup_family:{setup_eval.setup_family}",
        f"regime:{features.regime.value}",
        f"rr:{setup_eval.r_to_target:.2f}",
    ]
    if event_type in {"macro_announcement", "headline"} and event_mixed:
        reasons.append("context_uncertain")
    setup_type = "bullish_post_event_confirmation" if bullish else "bearish_post_event_confirmation"
    if setup_eval.setup_family == "failed_breakout_rejection":
        setup_type = f"{setup_type}_rejection"
    score = min(100.0, max(0.0, 60 + (setup_eval.r_to_target - 1.5) * 20 + min(20, confidence_score * 0.2)))
    return (
        CandidateSpec(
            symbol=sym,
            strategy=strategy,
            setup_type=setup_type,
            candidate_kind=setup_type,
            setup_score=score,
            reason_codes=reasons,
            confirmation_state="confirmed",
            event_id=event_id,
            direction_bias="long" if bullish else "short",
            legs=legs,
            is_event_driven=True,
            notes="Deterministic v1 Strategy A candidate.",
        ),
        None,
    )


def _sample_spread_legs(
    symbol: str,
    underlying: float,
    *,
    debit: bool,
    bullish: bool,
) -> list[dict[str, Any]]:
    """Template legs for simulation — not a live order ticket."""
    base = round(underlying / 5) * 5
    if bullish:
        long_strike = base
        short_strike = base + 5
        right = "C"
    else:
        long_strike = base
        short_strike = base - 5
        right = "P"
    if debit:
        return [
            {"symbol": symbol, "action": "buy", "strike": long_strike, "right": right},
            {"symbol": symbol, "action": "sell", "strike": short_strike, "right": right},
        ]
    return [
        {"symbol": symbol, "action": "sell", "strike": short_strike, "right": right},
        {"symbol": symbol, "action": "buy", "strike": long_strike, "right": right},
    ]


def _single_leg(symbol: str, underlying: float, *, bullish: bool) -> list[dict[str, Any]]:
    base = round(underlying / 5) * 5
    return [
        {
            "symbol": symbol,
            "action": "buy",
            "strike": base,
            "right": "C" if bullish else "P",
        }
    ]


def _should_use_debit_spread(option: dict[str, Any]) -> bool:
    flags = 0
    flags += int(bool(option.get("single_leg_exceeds_risk", False)))
    flags += int(bool(option.get("iv_rich", False)))
    flags += int(bool(option.get("move_not_explosive", True)))
    flags += int(bool(option.get("spread_improves_fit", True)))
    return flags >= 2
