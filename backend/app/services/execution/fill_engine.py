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
    structure: str = "single_leg",
    max_single_leg_chase_pct: float = 0.04,
    max_debit_spread_chase_pct: float = 0.08,
) -> FillResult:
    # v1 execution: limit-at-mid, then one price improvement inside chase cap.
    limit = float(mid or 0.0)
    if limit <= 0:
        limit = float((bid or 0.0) + (ask or 0.0)) / 2.0 if (bid and ask) else float(ask or bid or 1.0)
    improve = limit * (slippage_bps / 10_000)
    attempted = limit + improve if side.lower() == "buy" else limit - improve
    cap = max_single_leg_chase_pct if structure == "single_leg" else max_debit_spread_chase_pct
    if side.lower() == "buy":
        max_price = limit * (1.0 + cap)
        price = min(attempted, max_price)
    else:
        min_price = limit * (1.0 - cap)
        price = max(attempted, min_price)
    partial_qty = max(1, min(quantity, math.ceil(quantity * partial_max_fraction)))
    is_partial = partial_qty < quantity
    return FillResult(
        price=max(0.01, price),
        quantity=partial_qty,
        is_partial=is_partial,
        slip_bps_applied=((abs(price - limit) / max(limit, 1e-9)) * 10_000),
    )
