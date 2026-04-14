from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class QuoteTick:
    symbol: str
    bid: float | None = None
    ask: float | None = None
    last: float | None = None
    volume: float | None = None
    ts_ms: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class QuoteCache:
    """Thread-safe last-quote store fed by DXLink or mock loops."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._quotes: dict[str, QuoteTick] = {}

    def update(self, tick: QuoteTick) -> None:
        sym = tick.symbol.upper()
        with self._lock:
            self._quotes[sym] = tick

    def get(self, symbol: str) -> QuoteTick | None:
        with self._lock:
            return self._quotes.get(symbol.upper())

    def snapshot(self) -> dict[str, QuoteTick]:
        with self._lock:
            return dict(self._quotes)

    def spread_bps(self, symbol: str) -> float | None:
        t = self.get(symbol)
        if not t or t.bid is None or t.ask is None or t.bid <= 0:
            return None
        mid = (t.bid + t.ask) / 2
        if mid <= 0:
            return None
        return (t.ask - t.bid) / mid * 10_000
