"""OpenAI Responses API client for primary event triage/escalation."""

import json
import logging
from typing import Any

import httpx

from app.core.config import Settings
from app.schemas.event_analysis import EventAnalysisJudgment
from app.services.ai.prompt_builder import build_event_analysis_prompt
from app.services.ai.schema_registry import event_judgment_response_format
from app.services.events.normalized_packet import NormalizedEventPacket

log = logging.getLogger(__name__)


class OpenAIResponsesClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def analyze_event(
        self,
        packet: NormalizedEventPacket,
        *,
        escalation: bool = False,
    ) -> tuple[str, EventAnalysisJudgment]:
        if not self._settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY missing")
        model = (
            self._settings.openai_escalation_model
            if escalation
            else self._settings.openai_triage_model
        )
        body: dict[str, Any] = {
            "model": model,
            "input": build_event_analysis_prompt(packet),
            "text": {"format": event_judgment_response_format()},
        }
        url = f"{self._settings.openai_api_base_url.rstrip('/')}/responses"
        headers = {
            "Authorization": f"Bearer {self._settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self._settings.openai_request_timeout_seconds) as client:
            r = await client.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
        text = _extract_output_text(data)
        if not text:
            log.warning("openai empty output: %s", json.dumps(data)[:2000])
            raise ValueError("empty structured output")
        judgment = EventAnalysisJudgment.model_validate_json(text)
        return text, judgment


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
