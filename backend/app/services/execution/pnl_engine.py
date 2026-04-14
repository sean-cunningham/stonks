from app.models.active_position import ActivePosition


def update_unrealized(position: ActivePosition, mark_price: float, multiplier: int = 100) -> float:
    """Options-style P&L proxy: (mark - entry) * multiplier * qty for 1-lot."""
    pnl = (mark_price - position.average_entry_price) * multiplier * position.quantity
    position.unrealized_pnl = pnl
    position.market_value = mark_price * multiplier * position.quantity
    return pnl
