from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.services.market_data.quote_cache import QuoteCache
from app.strategies.spy_0dte_scalper.scanner import run_tick

log = logging.getLogger(__name__)


def run_spy_scalper_tick(db: Session, settings: Settings, quote_cache: QuoteCache) -> None:
    try:
        run_tick(db, settings, quote_cache)
    except Exception:
        log.exception("spy scalper tick failed")
