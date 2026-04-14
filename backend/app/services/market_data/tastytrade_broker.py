"""Concrete BrokerAdapter using TastytradeRestClient + TokenManager."""

from typing import Any

from app.core.config import Settings
from app.services.market_data.broker_adapter import BrokerAdapter
from app.services.market_data.tastytrade_rest import TastytradeRestClient
from app.services.market_data.token_manager import TokenManager


class TastytradeBrokerAdapter:
    def __init__(
        self,
        settings: Settings,
        tokens: TokenManager,
        rest: TastytradeRestClient | None = None,
    ) -> None:
        self._settings = settings
        self._tokens = tokens
        self._rest = rest or TastytradeRestClient(settings)

    async def refresh_oauth_if_needed(self) -> None:
        rt = self._settings.tastytrade_refresh_token
        if not rt:
            raise RuntimeError("TASTYTRADE_REFRESH_TOKEN not configured")
        if not self._tokens.oauth_needs_refresh():
            return
        body = await self._rest.refresh_access_token(rt)
        access = body.get("access_token")
        exp_in = int(body.get("expires_in", 3600))
        new_rt = body.get("refresh_token", rt)
        if not access:
            raise RuntimeError("OAuth response missing access_token")
        self._tokens.set_oauth(access, exp_in, new_rt)

    async def get_dxlink_token(self) -> dict[str, Any]:
        await self.refresh_oauth_if_needed()
        token = self._tokens.get_access_token()
        if not token:
            raise RuntimeError("No OAuth access token")
        raw = await self._rest.get_quote_streamer_tokens(token)
        data = raw.get("data") or raw
        token_str = data.get("token") or data.get("streamer-token")
        dx_url = self._settings.tastytrade_dx_url
        if not token_str:
            raise RuntimeError("Unexpected quote-token response shape")
        from app.core.clock import utc_now
        from datetime import timedelta

        self._tokens.set_dxlink(
            token_str,
            dx_url,
            expires_at=utc_now() + timedelta(hours=23),
        )
        return {"token": token_str, "dxlink_url": dx_url, "raw": raw}

    async def get_option_chain(self, symbol: str) -> dict[str, Any]:
        await self.refresh_oauth_if_needed()
        token = self._tokens.get_access_token()
        if not token:
            raise RuntimeError("No OAuth access token")
        return await self._rest.get_option_chain_compact(token, symbol)


def as_protocol(adapter: TastytradeBrokerAdapter) -> BrokerAdapter:
    return adapter  # structural subtyping
