from typing import Any

from app.services.events.normalized_packet import NormalizedEventPacket


def normalize_sec(raw: dict[str, Any]) -> NormalizedEventPacket:
    return NormalizedEventPacket(
        source=str(raw.get("source", "sec")),
        event_kind="sec_filing",
        symbol=str(raw["symbol"]).upper(),
        headline=str(raw.get("headline", "SEC filing")),
        body=raw.get("body"),
        dedupe_key=str(raw.get("cik_accession", raw.get("dedupe_key", "sec-unknown")))[:256],
        metadata=raw.get("metadata") or {},
    )
