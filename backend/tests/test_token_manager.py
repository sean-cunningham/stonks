from datetime import timedelta

from app.core.clock import utc_now
from app.services.market_data.token_manager import TokenManager


def test_oauth_refresh_window():
    tm = TokenManager(oauth_skew_seconds=3600)
    assert tm.oauth_needs_refresh() is True
    tm.set_oauth("a", expires_in_seconds=10_000, refresh_token="r")
    assert tm.oauth_needs_refresh() is False


def test_dxlink_refresh_window():
    tm = TokenManager(dx_skew_seconds=60, dx_token_ttl_hours=1)
    assert tm.dxlink_needs_refresh() is True
    tm.set_dxlink("t", "wss://x", expires_at=utc_now() + timedelta(hours=1))
    assert tm.dxlink_needs_refresh() is False
