from typing import Any

from app.services.events.normalized_packet import NormalizedEventPacket


def normalize_headline(raw: dict[str, Any]) -> NormalizedEventPacket:
    return NormalizedEventPacket(
        source=str(raw.get("source", "news")),
        event_kind="headline",
        symbol=str(raw["symbol"]).upper(),
        headline=str(raw.get("title") or raw.get("headline", "")),
        body=raw.get("summary"),
        dedupe_key=str(raw.get("id") or raw.get("url", "headline-unknown"))[:256],
        metadata={k: v for k, v in raw.items() if k not in ("symbol", "title", "headline", "summary", "id", "url")},
    )
