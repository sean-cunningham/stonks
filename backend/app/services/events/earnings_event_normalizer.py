from typing import Any

from app.services.events.normalized_packet import NormalizedEventPacket


def normalize_earnings(raw: dict[str, Any]) -> NormalizedEventPacket:
    return NormalizedEventPacket(
        source=str(raw.get("source", "earnings")),
        event_kind="earnings",
        symbol=str(raw["symbol"]).upper(),
        headline=str(raw.get("headline", "Earnings event")),
        body=raw.get("body"),
        dedupe_key=str(raw.get("dedupe_key", f"earn-{raw['symbol']}"))[:256],
        metadata=raw.get("metadata") or {},
    )
