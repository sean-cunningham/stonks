"""Bid/ask-aware fills with slippage and simplified partial fills."""

import math
from dataclasses import dataclass


@dataclass
class FillResult:
    price: float
    quantity: int
    is_partial: bool
    slip_bps_applied: float


def compute_open_fill(
    *,
    side: str,
    bid: float | None,
    ask: float | None,
    mid: float | None,
    quantity: int,
    slippage_bps: float,
    partial_max_fraction: float,
) -> FillResult:
    base = None
    if side.lower() == "buy":
        base = ask or mid or bid
    else:
        base = bid or mid or ask
    if base is None:
        base = float(mid or 0) or 1.0
    slip = base * (slippage_bps / 10_000)
    price = base + slip if side.lower() == "buy" else base - slip
    partial_qty = max(1, min(quantity, math.ceil(quantity * partial_max_fraction)))
    is_partial = partial_qty < quantity
    return FillResult(
        price=max(0.01, price),
        quantity=partial_qty,
        is_partial=is_partial,
        slip_bps_applied=slippage_bps,
    )
