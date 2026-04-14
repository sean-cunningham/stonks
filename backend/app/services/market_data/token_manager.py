from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.clock import utc_now


@dataclass
class OAuthTokens:
    access_token: str
    access_expires_at: datetime
    refresh_token: str


@dataclass
class DxLinkTokenInfo:
    token: str
    expires_at: datetime
    dxlink_url: str


class TokenManager:
    """Tracks OAuth access token and DXLink quote token; proactive refresh before expiry."""

    def __init__(
        self,
        *,
        oauth_skew_seconds: int = 120,
        dx_skew_seconds: int = 300,
        dx_token_ttl_hours: int = 23,
    ) -> None:
        self._oauth_skew = timedelta(seconds=oauth_skew_seconds)
        self._dx_skew = timedelta(seconds=dx_skew_seconds)
        self._dx_ttl = timedelta(hours=dx_token_ttl_hours)
        self._oauth: OAuthTokens | None = None
        self._dx: DxLinkTokenInfo | None = None

    def set_oauth(self, access_token: str, expires_in_seconds: int, refresh_token: str) -> None:
        now = utc_now()
        self._oauth = OAuthTokens(
            access_token=access_token,
            access_expires_at=now + timedelta(seconds=max(30, expires_in_seconds)),
            refresh_token=refresh_token,
        )

    def set_dxlink(self, token: str, dxlink_url: str, expires_at: datetime | None = None) -> None:
        exp = expires_at or (utc_now() + self._dx_ttl)
        self._dx = DxLinkTokenInfo(token=token, expires_at=exp, dxlink_url=dxlink_url)

    def oauth_needs_refresh(self) -> bool:
        if not self._oauth:
            return True
        return utc_now() >= (self._oauth.access_expires_at - self._oauth_skew)

    def dxlink_needs_refresh(self) -> bool:
        if not self._dx:
            return True
        return utc_now() >= (self._dx.expires_at - self._dx_skew)

    def get_access_token(self) -> str | None:
        return self._oauth.access_token if self._oauth else None

    def get_dxlink(self) -> DxLinkTokenInfo | None:
        return self._dx

    def clear(self) -> None:
        self._oauth = None
        self._dx = None


def parse_expires_header(expires_str: str | None) -> datetime | None:
    if not expires_str:
        return None
    try:
        return datetime.fromisoformat(expires_str.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None
