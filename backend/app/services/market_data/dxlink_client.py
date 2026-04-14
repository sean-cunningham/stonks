"""DXLink WebSocket client (minimal framing; extend per DXLink protocol docs)."""

import asyncio
import json
import logging
from inspect import isawaitable
from collections.abc import Awaitable, Callable
from typing import Any

import websockets
from websockets.client import WebSocketClientProtocol

from app.services.market_data.quote_cache import QuoteCache, QuoteTick

log = logging.getLogger(__name__)

OnQuote = Callable[[QuoteTick], Awaitable[None] | None]


class DXLinkClient:
    def __init__(
        self,
        *,
        url: str,
        quote_cache: QuoteCache,
        on_quote: OnQuote | None = None,
    ) -> None:
        self._url = url
        self._cache = quote_cache
        self._on_quote = on_quote
        self._ws: WebSocketClientProtocol | None = None
        self._stop = asyncio.Event()

    async def connect_and_listen(self, setup_messages: list[dict[str, Any]]) -> None:
        """Connect, send setup (e.g. AUTH + CHANNEL_REQUEST), process until stopped."""
        while not self._stop.is_set():
            try:
                async with websockets.connect(self._url, max_size=10_000_000) as ws:
                    self._ws = ws
                    for msg in setup_messages:
                        await ws.send(json.dumps(msg))
                    async for raw in ws:
                        await self._handle_message(raw)
            except Exception as e:
                log.warning("dxlink connection error: %s", e)
                await asyncio.sleep(2.0)

    def request_stop(self) -> None:
        self._stop.set()

    async def _handle_message(self, raw: str) -> None:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return
        sym = payload.get("eventSymbol") or payload.get("symbol")
        if not sym:
            return
        bid = _f(payload.get("bid"))
        ask = _f(payload.get("ask"))
        last = _f(payload.get("last") or payload.get("mark"))
        vol = _f(payload.get("dayVolume") or payload.get("volume"))
        tick = QuoteTick(
            symbol=str(sym).split(":")[-1][:16],
            bid=bid,
            ask=ask,
            last=last,
            volume=vol,
            raw=payload,
        )
        self._cache.update(tick)
        if self._on_quote:
            r = self._on_quote(tick)
            if isawaitable(r):
                await r


def _f(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None
