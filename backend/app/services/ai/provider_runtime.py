from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.config import Settings

log = logging.getLogger(__name__)

AI_PROVIDER_OPENAI = "openai"
AI_PROVIDER_XAI = "xai"


@dataclass(frozen=True)
class ProviderResolution:
    provider: str
    model: str
    strategy_id: str
    capability: str


def resolve_v1_provider(
    settings: Settings,
    *,
    strategy_id: str,
    capability: str,
    escalation: bool = False,
) -> ProviderResolution:
    provider = settings.ai_provider.strip().lower()
    if provider != AI_PROVIDER_OPENAI:
        log.error(
            "blocked disabled AI provider invocation strategy=%s capability=%s provider=%s",
            strategy_id,
            capability,
            provider,
        )
        raise RuntimeError(f"provider '{provider}' is disabled for v1 runtime")

    if not settings.openai_enabled:
        log.error(
            "blocked AI invocation with OPENAI_ENABLED=false strategy=%s capability=%s",
            strategy_id,
            capability,
        )
        raise RuntimeError("OPENAI_ENABLED=false blocks v1 AI runtime")

    model = settings.openai_escalation_model if escalation else settings.openai_triage_model
    log.info(
        "ai provider resolved strategy=%s capability=%s provider=%s model=%s",
        strategy_id,
        capability,
        provider,
        model,
    )
    if settings.xai_enabled:
        log.warning(
            "XAI_ENABLED=true ignored in v1 runtime strategy=%s capability=%s",
            strategy_id,
            capability,
        )

    return ProviderResolution(
        provider=provider,
        model=model,
        strategy_id=strategy_id,
        capability=capability,
    )
