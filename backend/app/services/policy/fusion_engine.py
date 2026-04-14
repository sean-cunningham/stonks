"""Fusion: deterministic candidate + AI + price + liquidity + config (checklist)."""

from dataclasses import dataclass

from app.core.enums import StrategyType
from app.models.active_position import ActivePosition
from app.models.candidate_trade import CandidateTrade
from app.models.event_analysis import EventAnalysis
from app.models.market_snapshot import MarketSnapshot
from app.services.strategy.liquidity_filters import LiquidityThresholds, passes_liquidity
from app.services.strategy.price_confirmation import (
    ai_bias_matches_direction,
    price_confirms_bias,
)


@dataclass
class FusionResult:
    ok: bool
    failed_rules: list[str]
    reasons: list[str]


ALLOWED = {
    StrategyType.LONG_CALL.value,
    StrategyType.LONG_PUT.value,
    StrategyType.DEBIT_SPREAD.value,
    StrategyType.CREDIT_SPREAD.value,
}


def _position_direction(p: ActivePosition) -> str:
    if p.strategy in ("long_call", "debit_spread"):
        return "long"
    if p.strategy in ("long_put", "credit_spread"):
        return "short"
    return "neutral"


def evaluate_fusion(
    *,
    candidate: CandidateTrade,
    snapshot: MarketSnapshot | None,
    event_row: EventAnalysis | None,
    open_positions: list[ActivePosition],
    liquidity: LiquidityThresholds | None = None,
) -> FusionResult:
    failed: list[str] = []
    reasons: list[str] = []

    def fail(code: str, msg: str) -> None:
        failed.append(code)
        reasons.append(msg)

    # 1 deterministic candidate exists
    if not candidate:
        return FusionResult(False, ["NO_CANDIDATE"], ["missing candidate"])

    # 7 symbol/strategy allowed
    if candidate.strategy not in ALLOWED:
        fail("STRATEGY_NOT_ALLOWED", f"strategy {candidate.strategy}")
    allowed_setups = {
        "bullish_post_event_confirmation",
        "bearish_post_event_confirmation",
        "anticipatory_macro_event",
    }
    if candidate.setup_type not in allowed_setups:
        fail("SETUP_NOT_ALLOWED", f"setup_type {candidate.setup_type}")
    if candidate.setup_score is None or candidate.setup_score < 60:
        fail("SETUP_SCORE_LOW", "setup score below minimum")
    from app.services.strategy.candidate_generator import DEFAULT_WATCHLIST

    if candidate.symbol.upper() not in DEFAULT_WATCHLIST:
        fail("SYMBOL_NOT_WATCHED", candidate.symbol)

    # 2 + 3 event-driven needs analysis + tradeability
    if candidate.is_event_driven:
        if not event_row:
            fail("MISSING_EVENT_ANALYSIS", "event-driven candidate requires analysis")
        elif not event_row.tradeability_flag:
            fail("AI_NOT_TRADEABLE", "tradeability_flag false")

    # 4 AI bias vs direction (when event present)
    bullish_trade = candidate.direction_bias == "long"
    if candidate.is_event_driven and event_row:
        if not ai_bias_matches_direction(event_row.direction_bias, bullish_trade=bullish_trade):
            fail("AI_BIAS_MISMATCH", "direction_bias does not support trade direction")
        if event_row.direction_bias == "mixed":
            fail("EVENT_MIXED", "event direction is mixed")

    # 5 spread / liquidity on snapshot
    th = liquidity or LiquidityThresholds()
    strike_n = None
    if snapshot and snapshot.extra:
        cl = snapshot.extra.get("chain_liquidity") or {}
        sc = cl.get("strike_count")
        strike_n = float(sc) if sc is not None else None
    if snapshot:
        ok_liq, lr = passes_liquidity(
            spread_bps=snapshot.spread_bps,
            volume=snapshot.volume,
            strike_count=strike_n,
            th=th,
        )
        if not ok_liq:
            fail("LIQUIDITY", lr or "liquidity")
        ref = snapshot.underlying_price or (
            (snapshot.bid + snapshot.ask) / 2 if snapshot.bid and snapshot.ask else None
        )
        ok_px, pr = price_confirms_bias(
            bullish_candidate=bullish_trade,
            bid=snapshot.bid,
            ask=snapshot.ask,
            last=snapshot.underlying_price,
            ref_price=ref,
        )
        if not ok_px:
            fail("PRICE_CONFIRMATION", pr or "price")
    else:
        fail("NO_SNAPSHOT", "market snapshot required")

    # 9 duplicate same-direction overlapping exposure on symbol
    for p in open_positions:
        if p.symbol != candidate.symbol:
            continue
        if _position_direction(p) == candidate.direction_bias:
            fail("DUPLICATE_EXPOSURE", f"existing {candidate.direction_bias} on {candidate.symbol}")
            break

    return FusionResult(ok=len(failed) == 0, failed_rules=failed, reasons=reasons)
