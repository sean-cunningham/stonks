from datetime import UTC, datetime

from app.models.active_position import ActivePosition
from app.services.execution.trade_management import update_trade_management


def _pos() -> ActivePosition:
    return ActivePosition(
        id=1,
        approved_trade_id=1,
        symbol="SPY",
        strategy="debit_spread",
        status="open",
        legs=[],
        quantity=2,
        average_entry_price=2.0,
        market_value=400.0,
        unrealized_pnl=0.0,
        initial_stop_price=1.5,
        emergency_premium_stop_pct=30.0,
        current_trailing_stop=1.5,
        breakeven_armed=False,
        partial_exit_taken=False,
        partial_exit_qty=0,
        thesis_expires_at=None,
        high_water_mark_price=2.0,
        low_water_mark_price=2.0,
        reached_1r=False,
        reached_1_5r=False,
        reached_2r=False,
        opened_at=datetime.now(UTC),
        closed_at=None,
    )


def test_trade_management_partial_trigger():
    p = _pos()
    update = update_trade_management(position=p, mark_price=2.9)
    assert update.take_partial
    assert update.partial_qty >= 1
