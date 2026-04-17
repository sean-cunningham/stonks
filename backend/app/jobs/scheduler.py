from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.exc import OperationalError

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.jobs.dxlink_feed import ensure_dxlink_feed_started
from app.jobs.event_loop import run_event_tick
from app.jobs.market_loop import run_market_tick
from app.jobs.reconciliation_loop import run_reconciliation_tick
from app.jobs.spy_scalper_reconciliation_loop import run_spy_scalper_reconciliation_tick
from app.jobs.token_refresh_loop import run_token_tick
from app.services.strategy.candidate_generator import DEFAULT_WATCHLIST
from app.strategies.spy_0dte_scalper.strategy import run_spy_scalper_tick
from app.jobs.strategy_schedule import scheduled_jobs_for_settings
from app.services.market_data.quote_cache import QuoteCache
from app.services.market_data.token_manager import TokenManager
from app.repositories.bot_state_repository import BotStateRepository
from app.repositories.strategy_bot_state_repository import SPY_SCALPER_SLUG, StrategyBotStateRepository

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
            run_market_tick(s, settings, _quote_cache, _token_manager)
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

    def spy_scalper_scan_job() -> None:
        s = SessionLocal()
        try:
            run_spy_scalper_tick(s, settings, _quote_cache)
        except Exception:
            log.exception("spy scalper scan failed")
        finally:
            s.close()

    def spy_scalper_recon_job() -> None:
        s = SessionLocal()
        try:
            run_spy_scalper_reconciliation_tick(s, settings, _quote_cache)
        except Exception:
            log.exception("spy scalper reconciliation failed")
        finally:
            s.close()

    _job_callables: dict[str, Callable[[], None]] = {
        "market_tick": market_job,
        "event_tick": event_job,
        "recon_tick": recon_job,
        "token_tick": token_job,
        "spy_scalper_scan": spy_scalper_scan_job,
        "spy_scalper_recon": spy_scalper_recon_job,
    }

    for meta in scheduled_jobs_for_settings(settings):
        fn = _job_callables.get(meta.job_id)
        if not fn:
            log.warning("scheduler: missing callable for job_id=%s", meta.job_id)
            continue
        _scheduler.add_job(
            fn,
            "interval",
            seconds=meta.interval_seconds,
            id=meta.job_id,
            replace_existing=True,
        )
        log.debug(
            "scheduler registered job_id=%s strategy_id=%s every=%ss",
            meta.job_id,
            meta.strategy_id,
            meta.interval_seconds,
        )
    _scheduler.start()
    log.info("background scheduler started")
    if settings.app_mode.value != "mock":
        try:
            run_token_tick(settings, _token_manager)
        except Exception:
            log.exception("initial tastytrade token refresh failed")
        ensure_dxlink_feed_started(get_settings, _token_manager, _quote_cache, list(DEFAULT_WATCHLIST))


def stop_background_jobs() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("background scheduler stopped")
    _scheduler = None


def _any_strategy_running() -> bool:
    s = SessionLocal()
    try:
        try:
            event_edge_running = BotStateRepository(s).get().state == "running"
        except OperationalError:
            event_edge_running = False
        try:
            spy_running = StrategyBotStateRepository(s).get_or_create(SPY_SCALPER_SLUG).state == "running"
        except OperationalError:
            spy_running = False
        return event_edge_running or spy_running
    finally:
        s.close()


def ensure_background_jobs_started(settings: Settings) -> None:
    if _any_strategy_running():
        start_background_jobs(settings)


def maybe_stop_background_jobs() -> None:
    if not _any_strategy_running():
        stop_background_jobs()
