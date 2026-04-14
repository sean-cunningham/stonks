from app.services.events.normalized_packet import NormalizedEventPacket


class MockXaiClient:
    async def enrich_event(self, packet: NormalizedEventPacket) -> tuple[str, dict]:
        payload = {
            "sentiment_bias": "mixed",
            "acceleration_flag": packet.event_kind in ("headline", "macro_announcement"),
            "rumor_risk_flag": False,
            "confidence_score": 44,
            "summary": "Secondary X context is mixed and non-authoritative. No elevated manipulation signal in mock mode.",
            "evidence_points": [f"symbol:{packet.symbol}", "mock-sidecar"],
        }
        import json

        return json.dumps(payload), payload
