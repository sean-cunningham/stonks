from typing import Any

from app.services.events.normalized_packet import NormalizedEventPacket


def normalize_macro(raw: dict[str, Any]) -> NormalizedEventPacket:
    return NormalizedEventPacket(
        source=str(raw.get("source", "macro")),
        event_kind="macro_announcement",
        symbol=str(raw.get("symbol", "SPY")).upper(),
        headline=str(raw.get("headline", "")),
        body=raw.get("body"),
        dedupe_key=str(raw.get("dedupe_key", "macro-unknown"))[:256],
        metadata=raw.get("metadata") or {},
    )
