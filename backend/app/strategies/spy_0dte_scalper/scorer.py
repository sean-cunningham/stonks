from __future__ import annotations

from typing import Any

from app.strategies.spy_0dte_scalper.setup_detector import DetectedSetup


def _cap(score: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, score))


def score_setup(setup: DetectedSetup, features: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Deterministic 0–100 base score with component caps."""
    bucket = str(features.get("time_bucket", "midday"))
    vol_ratio = float(features.get("vol_ratio", 1.0))
    impulse = abs(float(features.get("impulse_5m", 0.0)))

    structure = _cap(30 + impulse * 8000, 0, 35)
    volume = _cap(10 + (vol_ratio - 1.0) * 15, 0, 20)
    location = 15.0
    if setup.family in ("or_continuation", "compression_break"):
        location = 20.0
    time_adj = 10.0 if bucket == "open" else 8.0 if bucket == "midday" else 12.0

    base = structure + volume + location + time_adj
    base = _cap(base, 0, 100)

    exec_floor = 55.0
    if bucket == "close":
        exec_floor = 62.0
    elif bucket == "open":
        exec_floor = 58.0

    meta = {
        "structure": structure,
        "volume": volume,
        "location": location,
        "time_adj": time_adj,
        "exec_floor": exec_floor,
    }
    return float(base), meta
