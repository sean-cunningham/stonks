from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import Settings
from app.core.database import SessionLocal
from app.jobs.event_loop import run_event_tick
from app.jobs.market_loop import run_market_tick
from app.jobs.reconciliation_loop import run_reconciliation_tick
from app.jobs.token_refresh_loop import run_token_tick
from app.services.market_data.quote_cache import QuoteCache
from app.services.market_data.token_manager import TokenManager

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None
_quote_cache = QuoteCache()
_token_manager = TokenManager()


def get_quote_cache() -> QuoteCache:
    return _quote_cache


def get_token_manager() -> TokenManager:
    return _token_manager


def start_background_jobs(settings: Settings) -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        return
    _scheduler = BackgroundScheduler()

    def market_job() -> None:
        s = SessionLocal()
        try:
            run_market_tick(s, settings, _quote_cache)
        except Exception:
            log.exception("market tick failed")
        finally:
            s.close()

    def event_job() -> None:
        s = SessionLocal()
        try:
            run_event_tick(s, settings)
        except Exception:
            log.exception("event tick failed")
        finally:
            s.close()

    def recon_job() -> None:
        s = SessionLocal()
        try:
            run_reconciliation_tick(s)
        except Exception:
            log.exception("reconciliation failed")
        finally:
            s.close()

    def token_job() -> None:
        try:
            run_token_tick(settings, _token_manager)
        except Exception:
            log.exception("token tick failed")

    _scheduler.add_job(market_job, "interval", seconds=45, id="market_tick", replace_existing=True)
    _scheduler.add_job(event_job, "interval", seconds=120, id="event_tick", replace_existing=True)
    _scheduler.add_job(recon_job, "interval", seconds=300, id="recon_tick", replace_existing=True)
    _scheduler.add_job(token_job, "interval", hours=1, id="token_tick", replace_existing=True)
    _scheduler.start()
    log.info("background scheduler started")


def stop_background_jobs() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("background scheduler stopped")
    _scheduler = None
