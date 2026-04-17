import asyncio
import logging

from app.core.config import Settings
from app.services.market_data.tastytrade_broker import TastytradeBrokerAdapter
from app.services.market_data.token_manager import TokenManager

log = logging.getLogger(__name__)


def _tastytrade_configured(settings: Settings) -> bool:
    return bool(
        settings.tastytrade_refresh_token
        and settings.tastytrade_oauth_client_id
        and settings.tastytrade_oauth_client_secret
    )


async def refresh_tastytrade_market_tokens(settings: Settings, tm: TokenManager) -> None:
    broker = TastytradeBrokerAdapter(settings, tm)
    before_oauth = tm.oauth_needs_refresh()
    await broker.refresh_oauth_if_needed()
    if before_oauth and tm.get_access_token():
        log.info("tastytrade oauth refreshed")
    if tm.dxlink_needs_refresh():
        await broker.get_dxlink_token()
        log.info("dxlink quote token refreshed")


def run_token_tick(settings: Settings, tm: TokenManager) -> None:
    if settings.app_mode.value == "mock":
        return
    if not _tastytrade_configured(settings):
        return
    try:
        asyncio.run(refresh_tastytrade_market_tokens(settings, tm))
    except Exception:
        log.exception("tastytrade token refresh failed")
