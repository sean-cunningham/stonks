from typing import Any

from app.services.events.normalized_packet import NormalizedEventPacket


def normalize_transcript_snippet(raw: dict[str, Any]) -> NormalizedEventPacket:
    return NormalizedEventPacket(
        source=str(raw.get("source", "transcript")),
        event_kind="transcript",
        symbol=str(raw["symbol"]).upper(),
        headline=str(raw.get("headline", "Transcript excerpt")),
        body=str(raw.get("snippet", "")),
        dedupe_key=str(raw.get("dedupe_key", "tr-unknown"))[:256],
        metadata=raw.get("metadata") or {},
    )
