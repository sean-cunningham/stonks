"""Mock broker for mock mode and tests."""

from datetime import timedelta
from typing import Any

from app.core.clock import utc_now
from app.services.market_data.token_manager import TokenManager


class MockBrokerAdapter:
    async def refresh_oauth_if_needed(self) -> None:
        return

    async def get_dxlink_token(self) -> dict[str, Any]:
        return {
            "token": "mock-dx-token",
            "dxlink_url": "wss://mock.local/dx",
            "raw": {},
        }

    async def get_option_chain(self, symbol: str) -> dict[str, Any]:
        return {
            "symbol": symbol.upper(),
            "strikes": [],
            "mock": True,
        }


def prime_mock_tokens(tm: TokenManager) -> None:
    tm.set_oauth("mock-oauth", 3600, "mock-refresh")
    tm.set_dxlink(
        "mock-dx-token",
        "wss://mock.local/dx",
        expires_at=utc_now() + timedelta(hours=23),
    )
