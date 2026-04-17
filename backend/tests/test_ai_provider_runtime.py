from app.core.config import Settings
from app.services.ai.provider_runtime import resolve_v1_provider


def test_provider_resolution_defaults_to_openai():
    s = Settings()
    resolution = resolve_v1_provider(
        s,
        strategy_id="event-edge-v1",
        capability="context_classification",
    )
    assert resolution.provider == "openai"
    assert resolution.model == s.openai_triage_model


def test_provider_resolution_escalation_uses_escalation_model():
    s = Settings()
    resolution = resolve_v1_provider(
        s,
        strategy_id="event-edge-v1",
        capability="context_classification",
        escalation=True,
    )
    assert resolution.provider == "openai"
    assert resolution.model == s.openai_escalation_model


def test_provider_resolution_blocks_xai_in_v1():
    s = Settings()
    s.ai_provider = "xai"
    s.openai_enabled = True
    try:
        resolve_v1_provider(
            s,
            strategy_id="spy-0dte-scalper",
            capability="setup_scoring_support",
        )
        raise AssertionError("expected resolver to reject xai provider")
    except RuntimeError as e:
        assert "disabled for v1 runtime" in str(e)
