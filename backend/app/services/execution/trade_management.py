from dataclasses import dataclass

from app.models.active_position import ActivePosition


@dataclass
class TradeManagementUpdate:
    stop_price: float | None
    take_partial: bool
    partial_qty: int
    exit_all: bool
    reason: str | None


def update_trade_management(
    *,
    position: ActivePosition,
    mark_price: float,
) -> TradeManagementUpdate:
    entry = position.average_entry_price
    if entry <= 0:
        return TradeManagementUpdate(position.current_trailing_stop, False, 0, False, None)
    risk = abs(entry - (position.initial_stop_price or entry * 0.95))
    if risk <= 0:
        risk = entry * 0.05
    r_multiple = (mark_price - entry) / risk

    stop = position.current_trailing_stop or position.initial_stop_price
    take_partial = False
    partial_qty = 0

    if r_multiple >= 1.0 and not position.breakeven_armed:
        stop = max(stop or 0, entry)
        position.breakeven_armed = True
    if r_multiple >= 1.7 and not position.partial_exit_taken:
        take_partial = True
        partial_qty = max(1, position.quantity // 2)
    if r_multiple >= 2.0:
        stop = max(stop or 0, mark_price - risk * 0.8)
    if position.thesis_expires_at and position.thesis_expires_at <= position.opened_at:
        return TradeManagementUpdate(stop, take_partial, partial_qty, True, "thesis_expired")
    if stop is not None and mark_price <= stop:
        return TradeManagementUpdate(stop, take_partial, partial_qty, True, "trailing_stop_hit")
    return TradeManagementUpdate(stop, take_partial, partial_qty, False, None)
