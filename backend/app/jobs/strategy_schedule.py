"""Declarative metadata for background jobs (multi-strategy scheduler wiring)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.core.config import Settings


@dataclass(frozen=True)
class ScheduledJob:
    """One APScheduler interval job."""

    job_id: str
    interval_seconds: int
    strategy_id: str | None
    description: str


def scheduled_jobs_for_settings(settings: Settings) -> list[ScheduledJob]:
    """Return jobs in registration order (intervals unchanged from legacy behavior)."""
    spy_scan = max(15, int(settings.spy_scalper_job_interval_seconds))
    spy_recon = max(15, int(settings.spy_scalper_recon_interval_seconds))
    return [
        ScheduledJob(
            job_id="market_tick",
            interval_seconds=45,
            strategy_id="event-edge-v1",
            description="Strategy A market tick",
        ),
        ScheduledJob(
            job_id="event_tick",
            interval_seconds=120,
            strategy_id="event-edge-v1",
            description="Strategy A event ingestion",
        ),
        ScheduledJob(
            job_id="recon_tick",
            interval_seconds=300,
            strategy_id="event-edge-v1",
            description="Strategy A position reconciliation",
        ),
        ScheduledJob(
            job_id="token_tick",
            interval_seconds=3600,
            strategy_id=None,
            description="Broker token refresh (shared)",
        ),
        ScheduledJob(
            job_id="spy_scalper_scan",
            interval_seconds=spy_scan,
            strategy_id="spy-0dte-scalper",
            description="SPY 0DTE scalper scan",
        ),
        ScheduledJob(
            job_id="spy_scalper_recon",
            interval_seconds=spy_recon,
            strategy_id="spy-0dte-scalper",
            description="SPY 0DTE scalper reconciliation",
        ),
    ]
