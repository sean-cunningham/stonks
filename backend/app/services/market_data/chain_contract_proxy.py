"""Best-effort option contract proxy from Tastytrade nested chain JSON for v1_hard_veto."""

from __future__ import annotations

import math
from typing import Any


def _walk(obj: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        out.append(obj)
        for v in obj.values():
            out.extend(_walk(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_walk(v))
    return out


def best_effort_option_contract(chain: dict[str, Any], underlying: float | None) -> dict[str, Any] | None:
    """Pick a single-leg-like proxy near underlying for hard-veto fields; return None if not found."""
    if not chain or underlying is None or underlying <= 0:
        return None
    best: tuple[float, dict[str, Any]] | None = None
    for d in _walk(chain):
        strike = d.get("strike-price") or d.get("strikePrice") or d.get("strike")
        delta = d.get("delta") or d.get("optionDelta")
        if strike is None or delta is None:
            continue
        try:
            sk = float(strike)
            dl = abs(float(delta))
        except (TypeError, ValueError):
            continue
        if dl < 0.45 or dl > 0.65:
            continue
        dist = abs(sk - float(underlying))
        if best is None or dist < best[0]:
            bid = d.get("bid") or d.get("bidPrice")
            ask = d.get("ask") or d.get("askPrice")
            mid = None
            try:
                if bid is not None and ask is not None:
                    mid = (float(bid) + float(ask)) / 2.0
            except (TypeError, ValueError):
                mid = None
            if mid is None or mid <= 0:
                mid = max(float(bid or 0), float(ask or 0), 0.01)
            spread_abs = 0.0
            try:
                if bid is not None and ask is not None:
                    spread_abs = abs(float(ask) - float(bid))
            except (TypeError, ValueError):
                spread_abs = 0.05
            dte = 10
            for key in ("days-to-expiration", "daysToExpiration", "dte"):
                if key in d and d[key] is not None:
                    try:
                        dte = int(float(d[key]))
                        break
                    except (TypeError, ValueError):
                        pass
            oi = d.get("open-interest") or d.get("openInterest") or 0
            try:
                oi_f = float(oi)
            except (TypeError, ValueError):
                oi_f = 0.0
            chain_activity = min(1.0, math.log1p(max(0.0, oi_f)) / 10.0) if oi_f > 0 else 0.6
            best = (
                dist,
                {
                    "dte": max(7, min(14, dte)) if dte else 10,
                    "delta": dl,
                    "spread_abs": spread_abs,
                    "mid": mid,
                    "chain_activity_score": max(0.5, chain_activity),
                },
            )
    return best[1] if best else None
