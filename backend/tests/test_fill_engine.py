from app.services.execution.fill_engine import compute_open_fill


def test_buy_fill_uses_ask_and_slippage():
    fr = compute_open_fill(
        side="buy",
        bid=10.0,
        ask=10.1,
        mid=10.05,
        quantity=10,
        slippage_bps=100,
        partial_max_fraction=1.0,
    )
    assert fr.quantity == 10
    assert fr.price > 10.1
