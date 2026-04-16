from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class Bar1m:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def _et_minutes_since_open(now_utc: datetime) -> float:
    """Approximate RTH minutes since 9:30 ET using UTC-4/5 — mock-friendly flat offset."""
    return float((now_utc.minute + now_utc.hour * 60) % 390)


def synthesize_bars(mid: float, n: int = 90, seed: int | None = None) -> list[Bar1m]:
    rng = random.Random(seed)
    bars: list[Bar1m] = []
    px = mid
    now = datetime.now(timezone.utc)
    for i in range(n):
        drift = math.sin(i / 12.0) * mid * 0.0008
        shock = rng.uniform(-mid * 0.0012, mid * 0.0012)
        o = px
        c = max(0.01, o + drift + shock)
        hi = max(o, c) + abs(rng.gauss(0, mid * 0.0004))
        lo = min(o, c) - abs(rng.gauss(0, mid * 0.0004))
        vol = rng.uniform(50_000, 250_000)
        ts = now
        bars.append(Bar1m(ts=ts, open=o, high=hi, low=lo, close=c, volume=vol))
        px = c
    return bars


def compute_features(mid: float, bars: list[Bar1m]) -> dict[str, Any]:
    if not bars:
        return {"mid": mid, "vwap": mid, "or_high": mid, "or_low": mid, "vol_ratio": 1.0, "time_bucket": "midday"}
    closes = [b.close for b in bars]
    last = closes[-1]
    vwap_num = sum(b.close * b.volume for b in bars)
    vwap_den = sum(b.volume for b in bars) or 1.0
    vwap = vwap_num / vwap_den
    first_15 = bars[: min(15, len(bars))]
    or_high = max(b.high for b in first_15)
    or_low = min(b.low for b in first_15)
    vol_last = bars[-1].volume
    vol_base = sum(b.volume for b in bars[:-1]) / max(1, len(bars) - 1)
    vol_ratio = vol_last / vol_base if vol_base > 0 else 1.0
    mins = _et_minutes_since_open(bars[-1].ts)
    if mins < 60:
        time_bucket = "open"
    elif mins > 330:
        time_bucket = "close"
    else:
        time_bucket = "midday"
    impulse = (last - closes[-5]) / last if len(closes) >= 5 and last else 0.0
    compression = (max(closes[-20:]) - min(closes[-20:])) / last if len(closes) >= 20 else 0.01
    return {
        "mid": last,
        "vwap": vwap,
        "or_high": or_high,
        "or_low": or_low,
        "vol_ratio": float(vol_ratio),
        "time_bucket": time_bucket,
        "impulse_5m": float(impulse),
        "compression_20": float(compression),
        "distance_to_vwap": float((last - vwap) / last) if last else 0.0,
    }
