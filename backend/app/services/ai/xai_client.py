"""xAI Responses API sidecar for optional X/social enrichment."""

import json
import logging
from typing import Any

import httpx

from app.core.config import Settings
from app.services.events.normalized_packet import NormalizedEventPacket

log = logging.getLogger(__name__)


class XaiEnrichmentClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def enrich_event(self, packet: NormalizedEventPacket) -> tuple[str, dict[str, Any]]:
        if not self._settings.xai_api_key:
            raise RuntimeError("XAI_API_KEY missing")
        url = f"{self._settings.xai_api_base_url.rstrip('/')}/responses"
        prompt = _build_enrichment_prompt(packet)
        body: dict[str, Any] = {
            "model": self._settings.xai_enrichment_model,
            "input": prompt,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "x_enrichment",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "sentiment_bias": {"type": "string"},
                            "acceleration_flag": {"type": "boolean"},
                            "rumor_risk_flag": {"type": "boolean"},
                            "confidence_score": {"type": "integer"},
                            "summary": {"type": "string"},
                            "evidence_points": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": [
                            "sentiment_bias",
                            "acceleration_flag",
                            "rumor_risk_flag",
                            "confidence_score",
                            "summary",
                            "evidence_points",
                        ],
                        "additionalProperties": False,
                    },
                    "strict": True,
                }
            },
        }
        headers = {
            "Authorization": f"Bearer {self._settings.xai_api_key}",
            "Content-Type": "application/json",
        }
        timeout = self._settings.xai_request_timeout_seconds
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
        text = _extract_output_text(data)
        if not text:
            log.warning("xai empty output: %s", json.dumps(data)[:2000])
            raise ValueError("empty structured output")
        log.debug("xai raw output (truncated): %s", text[:2000])
        payload = json.loads(text)
        return text, payload


def _extract_output_text(data: dict[str, Any]) -> str | None:
    for item in data.get("output", []) or []:
        if item.get("type") == "message":
            for part in item.get("content", []) or []:
                if part.get("type") in ("output_text", "text"):
                    t = part.get("text")
                    if t:
                        return str(t)
    for item in data.get("output", []) or []:
        if item.get("type") == "output_text":
            t = item.get("text")
            if t:
                return str(t)
    return None


def _build_enrichment_prompt(packet: NormalizedEventPacket) -> str:
    payload = {
        "task": "Provide secondary X/social enrichment for an already-important event. Do not propose trades.",
        "rules": [
            "Return JSON only.",
            "Focus on acceleration, rumor/manipulation risk, and sentiment context.",
            "Keep summary to max two sentences.",
        ],
        "event_packet": packet.model_dump(mode="json"),
    }
    return json.dumps(payload, indent=2)
