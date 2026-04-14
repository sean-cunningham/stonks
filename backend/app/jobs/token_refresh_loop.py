import logging

from app.core.config import Settings
from app.services.market_data.token_manager import TokenManager

log = logging.getLogger(__name__)


def run_token_tick(settings: Settings, tm: TokenManager) -> None:
    if settings.app_mode.value == "mock":
        return
    if tm.oauth_needs_refresh() or tm.dxlink_needs_refresh():
        log.info("token refresh needed (wire tastytrade adapter in market_data mode)")
