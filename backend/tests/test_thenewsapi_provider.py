from app.core.config import Settings
from app.services.events.thenewsapi_provider import TheNewsApiProvider, _detect_symbol


def test_thenewsapi_disabled_returns_empty():
    s = Settings(
        thenewsapi_enable_real_calls=False,
        thenewsapi_api_key=None,
    )
    p = TheNewsApiProvider(s)
    assert p.poll() == []


def test_thenewsapi_symbol_detection():
    assert _detect_symbol("NVDA jumps after earnings", "") == "NVDA"
