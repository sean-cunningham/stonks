from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.services.ai.openai_client import _extract_output_text
from app.strategies.spy_0dte_scalper.config import ScalperEffectiveConfig
from app.strategies.spy_0dte_scalper.setup_detector import DetectedSetup

log = logging.getLogger(__name__)


class AiScalperVerdict(BaseModel):
    setup_type: str
    direction: str
    setup_score: int = Field(ge=0, le=100)
    urgency_score: int = Field(ge=0, le=100)
    regime: str
    pass_take: str
    reason_short: str
    invalidates_if: str


def _response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "name": "spy_scalper_gate",
        "schema": {
            "type": "object",
            "properties": {
                "setup_type": {"type": "string"},
                "direction": {"type": "string"},
                "setup_score": {"type": "integer"},
                "urgency_score": {"type": "integer"},
                "regime": {"type": "string"},
                "pass_take": {"type": "string"},
                "reason_short": {"type": "string"},
                "invalidates_if": {"type": "string"},
            },
            "required": [
                "setup_type",
                "direction",
                "setup_score",
                "urgency_score",
                "regime",
                "pass_take",
                "reason_short",
                "invalidates_if",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    }


def _mock_verdict(setup: DetectedSetup, base_score: float) -> AiScalperVerdict:
    take = "TAKE" if base_score >= 70 else "PASS"
    return AiScalperVerdict(
        setup_type=setup.family,
        direction=setup.direction,
        setup_score=int(min(100, max(0, round(base_score)))),
        urgency_score=55,
        regime="intraday",
        pass_take=take,
        reason_short="mock_structured_gate",
        invalidates_if="vwap_reclaim_fail",
    )


def _clamp_adjustment(raw: float) -> float:
    return max(-20.0, min(10.0, raw))


def run_ai_filter_sync(
    settings: Settings,
    cfg: ScalperEffectiveConfig,
    setup: DetectedSetup,
    base_score: float,
    features: dict[str, Any],
    *,
    ai_calls_today: int,
) -> tuple[float, AiScalperVerdict | None, str | None]:
    use_mock = settings.use_mock_openai or not settings.openai_enable_real_calls
    if ai_calls_today >= cfg.ai_max_calls_per_day:
        return 0.0, None, "ai_daily_cap"

    if use_mock:
        v = _mock_verdict(setup, base_score)
        adj = 5.0 if v.pass_take.upper() == "TAKE" and base_score >= 65 else -5.0
        if v.pass_take.upper() == "PASS":
            adj = -10.0
        return _clamp_adjustment(adj), v, None

    if not settings.openai_api_key:
        return 0.0, None, "no_openai_key"

    prompt = json.dumps(
        {
            "task": "spy_0dte_scalper_gate",
            "setup": {"family": setup.family, "direction": setup.direction},
            "base_score": base_score,
            "features": features,
            "rules": "Return JSON only. pass_take is TAKE or PASS. Scores 0-100.",
        }
    )
    body: dict[str, Any] = {
        "model": settings.openai_triage_model,
        "input": prompt,
        "text": {"format": _response_format()},
    }
    url = f"{settings.openai_api_base_url.rstrip('/')}/responses"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=settings.openai_request_timeout_seconds) as client:
            r = client.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
        text = _extract_output_text(data)
        if not text:
            return 0.0, None, "empty_ai_output"
        verdict = AiScalperVerdict.model_validate_json(text)
        adj = (verdict.setup_score - 50) / 10.0
        if verdict.pass_take.upper() == "PASS":
            adj = min(adj, -5.0)
        adj = _clamp_adjustment(adj)
        return adj, verdict, None
    except Exception:
        log.exception("spy scalper ai filter failed")
        return 0.0, None, "ai_error"
