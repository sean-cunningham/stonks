from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from app.core.enums import RegimeState
from app.models.market_snapshot import MarketSnapshot


@dataclass
class Bar:
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class V1FeatureSet:
    regime: RegimeState
    price: float
    vwap: float
    atr5m: float
    rel_volume_5m: float
    opening_range_high: float
    opening_range_low: float
    impulse_size: float
    pullback_depth: float
    overlap_5m_pct: float
    vwap_cross_count_1m: int
    structure_progression: bool
    levels: dict[str, float]
    bars_1m: list[Bar]
    bars_5m: list[Bar]
    bars_15m: list[Bar]


def _bars(extra: dict, key: str) -> list[Bar]:
    rows = extra.get(key) or []
    out: list[Bar] = []
    for r in rows:
        out.append(
            Bar(
                open=float(r.get("open", 0.0)),
                high=float(r.get("high", 0.0)),
                low=float(r.get("low", 0.0)),
                close=float(r.get("close", 0.0)),
                volume=float(r.get("volume", 0.0)),
            )
        )
    return out


def _atr14_5m(bars_5m: list[Bar]) -> float:
    if len(bars_5m) < 2:
        return 0.0
    trs: list[float] = []
    prev_close = bars_5m[0].close
    for b in bars_5m[1:]:
        tr = max(b.high - b.low, abs(b.high - prev_close), abs(b.low - prev_close))
        trs.append(tr)
        prev_close = b.close
    win = trs[-14:] if len(trs) > 14 else trs
    return mean(win) if win else 0.0


def _session_vwap(bars_1m: list[Bar], fallback: float) -> float:
    pv = 0.0
    vv = 0.0
    for b in bars_1m:
        typical = (b.high + b.low + b.close) / 3.0
        pv += typical * max(1.0, b.volume)
        vv += max(1.0, b.volume)
    if vv <= 0:
        return fallback
    return pv / vv


def _overlap_pct(last4: list[Bar]) -> float:
    if len(last4) < 4:
        return 0.0
    overlap = 0.0
    for i in range(1, len(last4)):
        a = last4[i - 1]
        b = last4[i]
        inter = max(0.0, min(a.high, b.high) - max(a.low, b.low))
        rng = max(1e-9, max(a.high, b.high) - min(a.low, b.low))
        overlap += inter / rng
    return (overlap / 3.0) * 100.0


def compute_v1_features(snapshot: MarketSnapshot) -> V1FeatureSet | None:
    extra = snapshot.extra or {}
    bars_1m = _bars(extra, "bars_1m")
    bars_5m = _bars(extra, "bars_5m")
    bars_15m = _bars(extra, "bars_15m")
    if len(bars_1m) < 12 or len(bars_5m) < 8 or len(bars_15m) < 3:
        return None
    price = snapshot.underlying_price or bars_1m[-1].close
    vwap = _session_vwap(bars_1m, price)
    atr = _atr14_5m(bars_5m)
    avg5_vol = mean(max(1.0, b.volume) for b in bars_5m[:-1]) if len(bars_5m) > 1 else 1.0
    rel_vol = (bars_5m[-1].volume / avg5_vol) if avg5_vol > 0 else 0.0
    opening_range_high = float(extra.get("opening_range_high", max(b.high for b in bars_1m[:15])))
    opening_range_low = float(extra.get("opening_range_low", min(b.low for b in bars_1m[:15])))
    prev_day_high = float(extra.get("prev_day_high", opening_range_high))
    prev_day_low = float(extra.get("prev_day_low", opening_range_low))
    premarket_high = float(extra.get("premarket_high", opening_range_high))
    premarket_low = float(extra.get("premarket_low", opening_range_low))

    # Recent impulse and pullback on 5m.
    recent5 = bars_5m[-6:]
    impulse_leg = max(b.high for b in recent5) - min(b.low for b in recent5)
    pullback_depth = max(0.0, max(b.high for b in recent5) - bars_5m[-1].close)
    overlap = _overlap_pct(bars_5m[-4:])
    vwap_cross = 0
    for i in range(-8, -1):
        a = bars_1m[i]
        b = bars_1m[i + 1]
        if (a.close - vwap) * (b.close - vwap) < 0:
            vwap_cross += 1
    struct_prog = (
        bars_5m[-1].high > bars_5m[-2].high and bars_5m[-2].high > bars_5m[-3].high
    ) or (
        bars_5m[-1].low < bars_5m[-2].low and bars_5m[-2].low < bars_5m[-3].low
    )

    # Regime rules.
    freeze = bool(extra.get("event_lockout_active", False)) or bool(extra.get("api_degraded", False))
    if extra.get("major_news_block_active"):
        freeze = True
    if len(bars_1m) >= 11:
        last_range = bars_1m[-1].high - bars_1m[-1].low
        avg10 = mean((b.high - b.low) for b in bars_1m[-11:-1])
        if avg10 > 0 and last_range > 1.75 * avg10 and bool(extra.get("immediately_after_event", False)):
            freeze = True
    if freeze:
        regime = RegimeState.FREEZE
    else:
        trend_up = (
            price > vwap
            and bars_15m[-1].close >= bars_15m[-2].close
            and (
                (
                    max(b.high for b in bars_5m[-6:]) == bars_5m[-1].high
                    and min(b.low for b in bars_5m[-6:]) == bars_5m[-6].low
                )
                or (
                    bars_5m[-1].close > opening_range_high
                    and bars_5m[-2].close > opening_range_high
                )
            )
            and rel_vol >= 0.9
            and vwap_cross <= 1
        )
        trend_down = (
            price < vwap
            and bars_15m[-1].close <= bars_15m[-2].close
            and (
                (
                    min(b.low for b in bars_5m[-6:]) == bars_5m[-1].low
                    and max(b.high for b in bars_5m[-6:]) == bars_5m[-6].high
                )
                or (
                    bars_5m[-1].close < opening_range_low
                    and bars_5m[-2].close < opening_range_low
                )
            )
            and rel_vol >= 0.9
            and vwap_cross <= 1
        )
        chop_flags = 0
        chop_flags += int(vwap_cross >= 3)
        chop_flags += int(overlap > 70.0)
        chop_flags += int(bool(extra.get("inside_opening_range_after_1015", False)))
        chop_flags += int(rel_vol < 0.9)
        chop_flags += int(not struct_prog)
        if trend_up:
            regime = RegimeState.TREND_UP
        elif trend_down:
            regime = RegimeState.TREND_DOWN
        elif chop_flags >= 2:
            regime = RegimeState.CHOP
        else:
            regime = RegimeState.CHOP

    return V1FeatureSet(
        regime=regime,
        price=price,
        vwap=vwap,
        atr5m=atr,
        rel_volume_5m=rel_vol,
        opening_range_high=opening_range_high,
        opening_range_low=opening_range_low,
        impulse_size=impulse_leg,
        pullback_depth=pullback_depth,
        overlap_5m_pct=overlap,
        vwap_cross_count_1m=vwap_cross,
        structure_progression=struct_prog,
        levels={
            "prev_day_high": prev_day_high,
            "prev_day_low": prev_day_low,
            "premarket_high": premarket_high,
            "premarket_low": premarket_low,
            "opening_range_high": opening_range_high,
            "opening_range_low": opening_range_low,
            "vwap": vwap,
        },
        bars_1m=bars_1m,
        bars_5m=bars_5m,
        bars_15m=bars_15m,
    )
