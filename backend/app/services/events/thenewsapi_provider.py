"""Optional TheNewsAPI supplemental provider."""

from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import Settings
from app.services.events.news_event_normalizer import normalize_headline
from app.services.events.normalized_packet import NormalizedEventPacket


class TheNewsApiProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._calls_today = 0
        self._day = datetime.now(UTC).date()

    def poll(self) -> list[NormalizedEventPacket]:
        if not self._settings.thenewsapi_enable_real_calls:
            return []
        if not self._settings.thenewsapi_api_key:
            return []
        today = datetime.now(UTC).date()
        if today != self._day:
            self._day = today
            self._calls_today = 0
        if self._calls_today >= self._settings.thenewsapi_request_limit_per_day:
            return []
        self._calls_today += 1

        url = "https://api.thenewsapi.com/v1/news/all"
        params = {
            "api_token": self._settings.thenewsapi_api_key,
            "language": "en",
            "limit": 5,
            "search": "SPY OR QQQ OR IWM OR NVDA OR TSLA OR AAPL OR AMZN OR META OR AMD OR SMCI",
        }
        with httpx.Client(timeout=30.0) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data: dict[str, Any] = r.json()
        rows = data.get("data", []) or []
        packets: list[NormalizedEventPacket] = []
        for row in rows:
            title = row.get("title")
            if not title:
                continue
            symbol = _detect_symbol(title, row.get("description") or "")
            if not symbol:
                continue
            uid = row.get("uuid") or row.get("url") or title
            packets.append(
                normalize_headline(
                    {
                        "id": f"thenewsapi|{uid}",
                        "source": "thenewsapi",
                        "symbol": symbol,
                        "title": title,
                        "summary": row.get("description"),
                        "url": row.get("url"),
                        "published_at": row.get("published_at"),
                    }
                )
            )
        return packets


def _detect_symbol(title: str, body: str) -> str | None:
    txt = f"{title} {body}".upper()
    for sym in ("SPY", "QQQ", "IWM", "NVDA", "TSLA", "AAPL", "AMZN", "META", "AMD", "SMCI"):
        if sym in txt:
            return sym
    return None
