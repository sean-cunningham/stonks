from pydantic import BaseModel


class ActivePositionRead(BaseModel):
    id: int
    symbol: str
    strategy: str
    status: str
    quantity: int
    average_entry_price: float
    market_value: float | None
    unrealized_pnl: float | None
    initial_stop_price: float | None
    emergency_premium_stop_pct: float | None
    current_trailing_stop: float | None
    breakeven_armed: bool
    partial_exit_taken: bool
    partial_exit_qty: int
    thesis_expires_at: str | None
    high_water_mark_price: float | None = None
    low_water_mark_price: float | None = None
    reached_1r: bool = False
    reached_1_5r: bool = False
    reached_2r: bool = False
    opened_at: str
    closed_at: str | None
    legs: list
