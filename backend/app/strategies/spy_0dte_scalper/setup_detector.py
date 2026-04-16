from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DetectedSetup:
    family: str
    direction: str  # "call" | "put"


OR_CONT = "or_continuation"
VWAP_RECLAIM = "vwap_reclaim_reject"
IMPULSE_PULLBACK = "impulse_pullback"
SWEEP_REVERSAL = "sweep_reversal"
COMPRESSION_BREAK = "compression_break"


def detect_setups(features: dict[str, Any]) -> list[DetectedSetup]:
    out: list[DetectedSetup] = []
    mid = float(features["mid"])
    vwap = float(features["vwap"])
    orh = float(features["or_high"])
    orl = float(features["or_low"])
    impulse = float(features.get("impulse_5m", 0.0))
    comp = float(features.get("compression_20", 0.01))
    dist_v = float(features.get("distance_to_vwap", 0.0))

    if mid > orh * 0.999 and impulse > 0.0005:
        out.append(DetectedSetup(family=OR_CONT, direction="call"))
    if mid < orl * 1.001 and impulse < -0.0005:
        out.append(DetectedSetup(family=OR_CONT, direction="put"))

    if mid > vwap * 1.0003 and dist_v > 0.0008:
        out.append(DetectedSetup(family=VWAP_RECLAIM, direction="call"))
    if mid < vwap * 0.9997 and dist_v < -0.0008:
        out.append(DetectedSetup(family=VWAP_RECLAIM, direction="put"))

    if impulse > 0.0012 and mid < vwap * 1.0005:
        out.append(DetectedSetup(family=IMPULSE_PULLBACK, direction="call"))
    if impulse < -0.0012 and mid > vwap * 0.9995:
        out.append(DetectedSetup(family=IMPULSE_PULLBACK, direction="put"))

    if mid > orh and impulse < 0:
        out.append(DetectedSetup(family=SWEEP_REVERSAL, direction="put"))
    if mid < orl and impulse > 0:
        out.append(DetectedSetup(family=SWEEP_REVERSAL, direction="call"))

    if comp < 0.004 and abs(impulse) > 0.0008:
        direction = "call" if impulse >= 0 else "put"
        out.append(DetectedSetup(family=COMPRESSION_BREAK, direction=direction))

    dedup: dict[tuple[str, str], DetectedSetup] = {}
    for s in out:
        dedup[(s.family, s.direction)] = s
    return list(dedup.values())
