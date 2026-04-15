"""Direct HTTP integration with Tastytrade REST API (OAuth2 refresh token flow).

Endpoint paths follow public documentation; response shapes may evolve — keep parsing defensive.
"""

from typing import Any

import httpx

from app.core.config import Settings


class TastytradeRestClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base = settings.tastytrade_api_base_url.rstrip("/")

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """Exchange refresh token for new access token."""
        url = f"{self._base}/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        auth = (
            self._settings.tastytrade_oauth_client_id or "",
            self._settings.tastytrade_oauth_client_secret or "",
        )
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                url,
                data=data,
                auth=httpx.BasicAuth(auth[0], auth[1]),
                headers={"Accept": "application/json"},
            )
            r.raise_for_status()
            return r.json()

    async def exchange_auth_code(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for OAuth tokens."""
        url = f"{self._base}/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._settings.tastytrade_oauth_redirect_uri or "",
        }
        auth = (
            self._settings.tastytrade_oauth_client_id or "",
            self._settings.tastytrade_oauth_client_secret or "",
        )
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                url,
                data=data,
                auth=httpx.BasicAuth(auth[0], auth[1]),
                headers={"Accept": "application/json"},
            )
            r.raise_for_status()
            return r.json()

    async def get_quote_streamer_tokens(self, access_token: str) -> dict[str, Any]:
        """Fetch DXLink / quote-streamer credentials (customer-scoped)."""
        url = f"{self._base}/api-quote-tokens"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            return r.json()

    async def get_option_chain_compact(
        self,
        access_token: str,
        symbol: str,
    ) -> dict[str, Any]:
        """Load compact option chain for underlying symbol (tastytrade nested resource)."""
        sym = symbol.upper()
        url = f"{self._base}/option-chains/{sym}/nested"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            return r.json()

    async def list_accounts(self, access_token: str) -> dict[str, Any]:
        """
        Fetch available accounts.
        Endpoint shapes can vary; keep defensive and return raw.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        urls = [
            f"{self._base}/customers/me/accounts",
            f"{self._base}/accounts",
        ]
        async with httpx.AsyncClient(timeout=60.0) as client:
            last_err: Exception | None = None
            for url in urls:
                try:
                    r = await client.get(url, headers=headers)
                    r.raise_for_status()
                    return r.json()
                except Exception as e:  # pragma: no cover - depends on upstream route shape
                    last_err = e
            if last_err:
                raise last_err
            raise RuntimeError("unable to fetch accounts")
