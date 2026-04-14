"""Setup-library deterministic candidate generation."""

from dataclasses import dataclass
from typing import Any

from app.core.config import Settings
from app.core.enums import StrategyType
from app.models.market_snapshot import MarketSnapshot
from app.services.strategy.confirmation_levels import LevelContext, confirm_direction
from app.services.strategy.cross_market_confirmation import index_cross_market_confirmation
from app.services.strategy.liquidity_filters import LiquidityThresholds, passes_liquidity
from app.services.strategy.setup_qualifier import setup_is_qualified
from app.services.strategy.setup_scorer import SetupInputs, score_setup

DEFAULT_WATCHLIST = (
    "SPY",
    "QQQ",
    "IWM",
    "NVDA",
    "TSLA",
    "AAPL",
    "AMZN",
    "META",
    "AMD",
    "SMCI",
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
    levels: LevelContext | None = None,
    cross_market: dict[str, float | None] | None = None,
    rumor_risk_flag: bool = False,
    anticipatory_allowed: bool = False,
    liquidity: LiquidityThresholds | None = None,
) -> tuple[CandidateSpec | None, str | None]:
    th = liquidity or LiquidityThresholds()
    sym = snap.symbol.upper()
    if sym not in DEFAULT_WATCHLIST:
        return None, "symbol_not_watched"

    strike_n = _strike_count_from_snapshot(snap)
    ok, reason = passes_liquidity(
        spread_bps=snap.spread_bps,
        volume=snap.volume,
        strike_count=strike_n,
        th=th,
    )
    if not ok:
        return None, reason or "liquidity"

    underlying = snap.underlying_price
    if underlying is None and snap.bid and snap.ask:
        underlying = (snap.bid + snap.ask) / 2
    if underlying is None:
        return None, "no_underlying"

    bullish = direction_bias == "bullish"
    lv = levels or LevelContext(vwap=underlying, round_number=round(underlying / 5) * 5, major_strike=round(underlying / 5) * 5)
    confirmation_ok = confirm_direction(bullish=bullish, price=underlying, levels=lv)
    cm = cross_market or {}
    cross_ok = index_cross_market_confirmation(
        symbol=sym,
        bullish=bullish,
        es_change_pct=cm.get("es_change_pct"),
        nq_change_pct=cm.get("nq_change_pct"),
        vix_change_pct=cm.get("vix_change_pct"),
        yield_change_bps=cm.get("yield_change_bps"),
        breadth_ratio=cm.get("breadth_ratio"),
    )
    score, reasons = score_setup(
        SetupInputs(
            materiality_score=materiality_score,
            confidence_score=confidence_score,
            liquidity_ok=ok,
            confirmation_ok=confirmation_ok,
            cross_market_ok=cross_ok,
            rumor_risk_flag=rumor_risk_flag,
            event_mixed=event_mixed,
        )
    )
    if event_type == "macro_announcement" and anticipatory_allowed and not confirmation_ok:
        setup_type = "anticipatory_macro_event"
    elif bullish:
        setup_type = "bullish_post_event_confirmation"
    else:
        setup_type = "bearish_post_event_confirmation"
    is_ok, qual_reason = setup_is_qualified(
        setup_type=setup_type,
        setup_score=score,
        event_type=event_type,
        event_mixed=event_mixed,
    )
    if not is_ok:
        return None, qual_reason

    legs = _sample_spread_legs(sym, underlying, debit=True, bullish=bullish)
    strategy = StrategyType.DEBIT_SPREAD
    if setup_type == "anticipatory_macro_event":
        strategy = StrategyType.CREDIT_SPREAD
        legs = _sample_spread_legs(sym, underlying, debit=False, bullish=bullish)
        reasons.append("anticipatory_smaller_size_required")
    return (
        CandidateSpec(
            symbol=sym,
            strategy=strategy,
            setup_type=setup_type,
            candidate_kind=setup_type,
            setup_score=score,
            reason_codes=reasons,
            confirmation_state="confirmed" if confirmation_ok else "anticipatory",
            event_id=event_id,
            direction_bias="long" if bullish else "short",
            legs=legs,
            is_event_driven=True,
            notes="Setup-library candidate generated.",
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
