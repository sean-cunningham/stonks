from __future__ import annotations

from dataclasses import dataclass

from app.core.enums import RegimeState
from app.services.strategy.v1_feature_engine import V1FeatureSet


@dataclass
class SetupEvaluation:
    ok: bool
    setup_family: str | None
    direction: str | None
    stop_price: float | None
    target_price: float | None
    r_to_target: float
    reason_codes: list[str]


def _continuation_setup(f: V1FeatureSet, *, bullish: bool, context_block: bool) -> SetupEvaluation:
    reasons: list[str] = []
    if context_block:
        reasons.append("context_block")
    if bullish and f.regime != RegimeState.TREND_UP:
        reasons.append("regime_not_trend_up")
    if not bullish and f.regime != RegimeState.TREND_DOWN:
        reasons.append("regime_not_trend_down")
    if f.atr5m <= 0:
        reasons.append("atr_invalid")
    impulse_min = 0.75 * max(f.atr5m, 1e-9)
    if f.impulse_size < impulse_min:
        reasons.append("impulse_too_small")
    if f.impulse_size <= 0:
        reasons.append("impulse_invalid")
    else:
        retrace = f.pullback_depth / f.impulse_size
        if retrace < 0.20 or retrace > 0.45:
            reasons.append("pullback_depth_outside_range")
    recent_pullback = f.bars_1m[-5:-1]
    if len(recent_pullback) > 4:
        reasons.append("pullback_too_long")
    trigger_level = max(b.high for b in recent_pullback) if bullish else min(b.low for b in recent_pullback)
    trigger_bar = f.bars_1m[-1]
    prior_bar = f.bars_1m[-2]
    if bullish and trigger_bar.high <= trigger_level:
        reasons.append("trigger_not_broken")
    if (not bullish) and trigger_bar.low >= trigger_level:
        reasons.append("trigger_not_broken")
    if trigger_bar.volume < prior_bar.volume:
        reasons.append("trigger_volume_weak")
    if bullish:
        stop = min(b.low for b in recent_pullback) - 0.05 * f.atr5m
        entry = trigger_bar.close
        target = entry + 1.5 * (entry - stop)
    else:
        stop = max(b.high for b in recent_pullback) + 0.05 * f.atr5m
        entry = trigger_bar.close
        target = entry - 1.5 * (stop - entry)
    risk = abs(entry - stop)
    rr = (abs(target - entry) / risk) if risk > 0 else 0.0
    if rr < 1.5:
        reasons.append("reward_below_1_5r")
    return SetupEvaluation(
        ok=len(reasons) == 0,
        setup_family="trend_continuation",
        direction="long" if bullish else "short",
        stop_price=stop,
        target_price=target,
        r_to_target=rr,
        reason_codes=reasons,
    )


def _rejection_setup(f: V1FeatureSet, *, bullish: bool, context_block: bool) -> SetupEvaluation:
    reasons: list[str] = []
    if context_block:
        reasons.append("context_block")
    if f.regime == RegimeState.FREEZE:
        reasons.append("regime_freeze")
    atr = max(1e-9, f.atr5m)
    trigger = f.bars_1m[-1]
    prior = f.bars_1m[-2]
    tested_level = f.levels["vwap"]
    probe = (tested_level - trigger.low) if bullish else (trigger.high - tested_level)
    if probe < 0.03 * atr:
        reasons.append("probe_too_shallow")
    reclaimed = trigger.close > tested_level if bullish else trigger.close < tested_level
    if not reclaimed:
        reasons.append("no_reclaim")
    rng = max(1e-9, trigger.high - trigger.low)
    wick = (trigger.close - trigger.low) if bullish else (trigger.high - trigger.close)
    if wick < 0.25 * rng:
        reasons.append("wick_too_small")
    if trigger.volume < prior.volume:
        reasons.append("trigger_volume_weak")
    entry = trigger.close
    if bullish:
        stop = trigger.low - 0.03 * atr
        target = min(f.levels["prev_day_high"], entry + 1.8 * (entry - stop))
    else:
        stop = trigger.high + 0.03 * atr
        target = max(f.levels["prev_day_low"], entry - 1.8 * (stop - entry))
    risk = abs(entry - stop)
    rr = abs(target - entry) / risk if risk > 0 else 0.0
    if rr < 1.5:
        reasons.append("reward_below_1_5r")
    return SetupEvaluation(
        ok=len(reasons) == 0,
        setup_family="failed_breakout_rejection",
        direction="long" if bullish else "short",
        stop_price=stop,
        target_price=target,
        r_to_target=rr,
        reason_codes=reasons,
    )


def evaluate_strategy_a_setups(
    f: V1FeatureSet,
    *,
    bullish: bool,
    context_block: bool,
) -> SetupEvaluation:
    continuation = _continuation_setup(f, bullish=bullish, context_block=context_block)
    if continuation.ok:
        return continuation
    rejection = _rejection_setup(f, bullish=bullish, context_block=context_block)
    if rejection.ok:
        return rejection
    return SetupEvaluation(
        ok=False,
        setup_family=None,
        direction="long" if bullish else "short",
        stop_price=None,
        target_price=None,
        r_to_target=0.0,
        reason_codes=list(dict.fromkeys(continuation.reason_codes + rejection.reason_codes)),
    )
