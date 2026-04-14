import json

from app.services.events.normalized_packet import NormalizedEventPacket


def build_event_analysis_prompt(packet: NormalizedEventPacket) -> str:
    payload = {
        "task": "Analyze the event for trading relevance. Output JSON only matching the provided schema.",
        "rules": [
            "Do not propose orders or position sizes.",
            "Use only the supplied packet; do not invent facts.",
            "narrative_summary: at most two sentences.",
            "Scores 0-100 where applicable.",
        ],
        "event_packet": packet.model_dump(mode="json"),
    }
    return json.dumps(payload, indent=2)
