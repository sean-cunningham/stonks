"""Background DXLink WebSocket feed: live equity quotes into QuoteCache (non-mock modes).

Protocol aligned with tastytrade/tastytrade DXLinkStreamer (SETUP, AUTH, FEED channels).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import threading
import time
from typing import Any, Callable

import websockets

from app.core.config import Settings
from app.jobs.token_refresh_loop import _tastytrade_configured, refresh_tastytrade_market_tokens
from app.services.market_data.quote_cache import QuoteCache, QuoteTick
from app.services.market_data.token_manager import TokenManager

log = logging.getLogger(__name__)

# Matches tastytrade DXLinkStreamer MAP_EVENTS channel assignment (i * 2 + 1).
QUOTE_CHANNEL = 7
DXLINK_VERSION = "0.1-DXF-JS/0.3.0"

_QUOTE_ACCEPT_FIELDS: dict[str, list[str]] = {
    "Quote": [
        "eventSymbol",
        "eventTime",
        "sequence",
        "timeNanoPart",
        "bidTime",
        "bidExchangeCode",
        "askTime",
        "askExchangeCode",
        "bidPrice",
        "askPrice",
        "bidSize",
        "askSize",
    ]
}

_feed_started = False
_feed_lock = threading.Lock()


def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        if isinstance(v, str) and v in ("NaN", "Infinity", "-Infinity"):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_compact_quote_row(keys: list[str], values: list[Any]) -> dict[str, Any]:
    return dict(zip(keys, values, strict=False))


def _quote_row_to_tick(row: dict[str, Any]) -> QuoteTick | None:
    sym_raw = row.get("eventSymbol") or row.get("event_symbol")
    if not sym_raw:
        return None
    sym = str(sym_raw).split(":")[-1].replace("&", "").strip().upper()[:16]
    bid = _to_float(row.get("bidPrice") or row.get("bid_price"))
    ask = _to_float(row.get("askPrice") or row.get("ask_price"))
    last = (bid + ask) / 2.0 if bid is not None and ask is not None and bid > 0 and ask > 0 else None
    bs = _to_float(row.get("bidSize") or row.get("bid_size"))
    a_s = _to_float(row.get("askSize") or row.get("ask_size"))
    vol = bs or a_s
    return QuoteTick(symbol=sym, bid=bid, ask=ask, last=last, volume=vol, raw=row)


def _handle_feed_data(payload: list[Any], quote_cache: QuoteCache, last_info_log: dict[str, float]) -> None:
    if not payload or len(payload) < 2:
        return
    head = payload[0]
    if isinstance(head, str):
        msg_type = head
    elif isinstance(head, list) and head and isinstance(head[0], str):
        msg_type = head[0]
    else:
        return
    body = payload[1]
    if msg_type != "Quote" or not isinstance(body, list):
        return
    keys = _QUOTE_ACCEPT_FIELDS["Quote"]
    n = len(keys)
    if not body or len(body) % n != 0:
        return
    now = time.monotonic()
    for i in range(0, len(body), n):
        chunk = body[i : i + n]
        if len(chunk) != n:
            break
        row = _parse_compact_quote_row(keys, chunk)
        tick = _quote_row_to_tick(row)
        if not tick:
            continue
        quote_cache.update(tick)
        if now - last_info_log.get(tick.symbol, 0.0) >= 30.0:
            last_info_log[tick.symbol] = now
            log.info(
                "dxlink quote tick symbol=%s bid=%s ask=%s last=%s",
                tick.symbol,
                tick.bid,
                tick.ask,
                tick.last,
            )


async def _heartbeat(ws: Any) -> None:
    while True:
        await asyncio.sleep(30.0)
        try:
            await ws.send(json.dumps({"type": "KEEPALIVE", "channel": 0}))
        except Exception:
            log.warning("dxlink keepalive send failed")
            return


async def _run_dxlink_session(
    settings: Settings,
    tm: TokenManager,
    quote_cache: QuoteCache,
    symbols: list[str],
) -> None:
    if not _tastytrade_configured(settings):
        log.warning("dxlink feed skipped: tastytrade credentials incomplete")
        return

    await refresh_tastytrade_market_tokens(settings, tm)
    dx = tm.get_dxlink()
    if not dx or not dx.token:
        log.warning("dxlink feed skipped: no dxlink token after refresh")
        return

    url = dx.dxlink_url
    token = dx.token
    sym_list = [s.strip().upper() for s in symbols if s.strip()]

    log.info("dxlink connecting url=%s symbols=%s", url, sym_list)

    hb_task: asyncio.Task[None] | None = None
    last_info: dict[str, float] = {}

    async with websockets.connect(url, ping_interval=None, close_timeout=10) as ws:
        await ws.send(
            json.dumps(
                {
                    "type": "SETUP",
                    "channel": 0,
                    "keepaliveTimeout": 60,
                    "acceptKeepaliveTimeout": 60,
                    "version": DXLINK_VERSION,
                }
            )
        )

        authorized = False
        while not authorized:
            raw = await asyncio.wait_for(ws.recv(), timeout=60.0)
            msg = json.loads(raw)
            mtype = msg.get("type")
            if mtype == "SETUP":
                await ws.send(json.dumps({"type": "AUTH", "channel": 0, "token": token}))
            elif mtype == "AUTH_STATE" and msg.get("state") == "AUTHORIZED":
                authorized = True
            elif mtype == "ERROR":
                raise RuntimeError(msg.get("message", "dxlink ERROR"))
            elif mtype == "KEEPALIVE":
                continue
            elif mtype == "FEED_CONFIG":
                continue

        await ws.send(
            json.dumps(
                {
                    "type": "CHANNEL_REQUEST",
                    "channel": QUOTE_CHANNEL,
                    "service": "FEED",
                    "parameters": {"contract": "AUTO"},
                }
            )
        )

        quote_ready = False
        while not quote_ready:
            raw = await asyncio.wait_for(ws.recv(), timeout=60.0)
            msg = json.loads(raw)
            mtype = msg.get("type")
            if mtype == "CHANNEL_OPENED" and int(msg.get("channel", -1)) == QUOTE_CHANNEL:
                quote_ready = True
            elif mtype == "ERROR":
                raise RuntimeError(msg.get("message", "dxlink ERROR"))
            elif mtype == "KEEPALIVE":
                continue
            elif mtype == "FEED_CONFIG":
                continue

        await ws.send(
            json.dumps(
                {
                    "type": "FEED_SETUP",
                    "channel": QUOTE_CHANNEL,
                    "acceptAggregationPeriod": 0.1,
                    "acceptDataFormat": "COMPACT",
                    "acceptEventFields": _QUOTE_ACCEPT_FIELDS,
                }
            )
        )
        add = [{"symbol": s, "type": "Quote"} for s in sym_list]
        await ws.send(
            json.dumps(
                {
                    "type": "FEED_SUBSCRIPTION",
                    "channel": QUOTE_CHANNEL,
                    "add": add,
                }
            )
        )
        log.info("dxlink subscribed Quote for %s", sym_list)

        hb_task = asyncio.create_task(_heartbeat(ws))
        try:
            while True:
                raw = await ws.recv()
                msg = json.loads(raw)
                mtype = msg.get("type")
                if mtype == "FEED_DATA":
                    _handle_feed_data(msg.get("data") or [], quote_cache, last_info)
                elif mtype == "ERROR":
                    raise RuntimeError(msg.get("message", "dxlink ERROR"))
                elif mtype in ("KEEPALIVE", "FEED_CONFIG", "CHANNEL_OPENED"):
                    continue
        finally:
            if hb_task is not None:
                hb_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await hb_task


async def _dxlink_forever(
    settings_getter: Callable[[], Settings],
    tm: TokenManager,
    quote_cache: QuoteCache,
    symbols: list[str],
) -> None:
    while True:
        settings = settings_getter()
        if settings.app_mode.value == "mock":
            await asyncio.sleep(5.0)
            continue
        try:
            await _run_dxlink_session(settings, tm, quote_cache, symbols)
        except Exception:
            log.exception("dxlink session ended with error; reconnecting in 5s")
            await asyncio.sleep(5.0)


def _thread_entry(
    settings_getter: Callable[[], Settings],
    tm: TokenManager,
    quote_cache: QuoteCache,
    symbols: list[str],
) -> None:
    asyncio.run(_dxlink_forever(settings_getter, tm, quote_cache, symbols))


def ensure_dxlink_feed_started(
    settings_getter: Callable[[], Settings],
    tm: TokenManager,
    quote_cache: QuoteCache,
    symbols: list[str],
) -> None:
    global _feed_started
    settings = settings_getter()
    if settings.app_mode.value == "mock":
        return
    if not _tastytrade_configured(settings):
        return
    with _feed_lock:
        if _feed_started:
            return
        t = threading.Thread(
            target=_thread_entry,
            args=(settings_getter, tm, quote_cache, symbols),
            name="dxlink-feed",
            daemon=True,
        )
        t.start()
        _feed_started = True
        log.info("dxlink background feed thread started")
