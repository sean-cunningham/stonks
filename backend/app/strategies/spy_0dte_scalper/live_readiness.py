"""Live paper readiness and dashboard runtime facts for SPY 0DTE scalper + shared fields."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import Settings
from app.core.enums import AppMode
from app.models.market_snapshot import MarketSnapshot
from app.services.market_data.quote_cache import QuoteCache, QuoteTick

MAX_SPY_QUOTE_AGE_SEC = 120.0

SPY_SYNTHETIC_BLOCK_REASON = (
    "spy_scalper_prototype_synthetic_bars_mock_chain_disabled_outside_APP_MODE_mock"
)


@dataclass
class SpyRuntimeHealth:
    """Serialized to dashboard `extensions.runtime_health`."""

    safe_to_trade: bool
    block_reason: str | None
    last_spy_quote_age_sec: float | None
    last_chain_snapshot_status: str
    app_mode: str
    api_degraded: bool | None
    chain_snapshot_age_sec: float | None
    last_quote_tick_iso: str | None
    live_candidate_pipeline_enabled: bool
    spy_scalper_synthetic_blocked: bool
    spy_scalper_synthetic_block_reason: str | None

    def as_extension_dict(self) -> dict[str, Any]:
        return asdict(self)


def spy_underlying_mid(quote_cache: QuoteCache) -> float | None:
    return _mid_from_tick(quote_cache.get("SPY"))


def _mid_from_tick(t: QuoteTick | None) -> float | None:
    if not t:
        return None
    if t.bid and t.ask and t.bid > 0 and t.ask > 0:
        return (t.bid + t.ask) / 2
    if t.last and t.last > 0:
        return float(t.last)
    return None


def _quote_age_sec(t: QuoteTick | None) -> float | None:
    if not t or t.ts_ms is None:
        return None
    return max(0.0, utc_now().timestamp() - (t.ts_ms / 1000.0))


def _tick_iso(t: QuoteTick | None) -> str | None:
    if not t or t.ts_ms is None:
        return None
    return datetime.fromtimestamp(t.ts_ms / 1000.0, tz=timezone.utc).isoformat()


def latest_spy_snapshot_row(db: Session) -> MarketSnapshot | None:
    return db.scalars(
        select(MarketSnapshot).where(MarketSnapshot.symbol == "SPY").order_by(MarketSnapshot.id.desc()).limit(1),
    ).first()


def _chain_snapshot_age_sec(extra: dict) -> float | None:
    ct = extra.get("chain_ts_epoch")
    if ct is None:
        return None
    try:
        return max(0.0, time.time() - float(ct))
    except (TypeError, ValueError):
        return None


def evaluate_spy_live_paper_readiness(
    db: Session,
    settings: Settings,
    quote_cache: QuoteCache,
) -> SpyRuntimeHealth:
    """Facts for dashboards. SPY scan/recon only run in MOCK; live modes stay fail-closed here."""
    tick = quote_cache.get("SPY")
    q_age = _quote_age_sec(tick)
    tick_iso = _tick_iso(tick)
    snap = latest_spy_snapshot_row(db)
    extra: dict = {}
    if snap and isinstance(snap.extra, dict):
        extra = snap.extra
    chain_age = _chain_snapshot_age_sec(extra)
    api_deg_raw = extra.get("api_degraded")
    api_deg_bool = bool(api_deg_raw) if api_deg_raw is not None else None

    pipeline = settings.live_candidate_pipeline_enabled

    if settings.app_mode == AppMode.MOCK:
        if not snap:
            chain_status = "no_snapshot"
        elif extra.get("mock"):
            chain_status = "mock_snapshot"
        elif extra.get("api_degraded"):
            chain_status = "degraded"
        else:
            chain_status = "ok"
        return SpyRuntimeHealth(
            safe_to_trade=True,
            block_reason=None,
            last_spy_quote_age_sec=q_age,
            last_chain_snapshot_status=chain_status,
            app_mode=str(settings.app_mode.value),
            api_degraded=api_deg_bool,
            chain_snapshot_age_sec=chain_age,
            last_quote_tick_iso=tick_iso,
            live_candidate_pipeline_enabled=pipeline,
            spy_scalper_synthetic_blocked=False,
            spy_scalper_synthetic_block_reason=None,
        )

    if not snap:
        chain_status = "missing"
    elif extra.get("api_degraded"):
        chain_status = "degraded"
    else:
        chain_status = "ok"

    mid = _mid_from_tick(tick)
    extras: list[str] = [SPY_SYNTHETIC_BLOCK_REASON]
    if mid is None or mid <= 0:
        extras.append("missing_spy_quote")
    if q_age is not None and q_age > MAX_SPY_QUOTE_AGE_SEC:
        extras.append("stale_spy_quote")
    if not snap:
        extras.append("missing_spy_snapshot")
    elif extra.get("api_degraded"):
        extras.append("api_degraded")

    return SpyRuntimeHealth(
        safe_to_trade=False,
        block_reason=";".join(extras),
        last_spy_quote_age_sec=q_age,
        last_chain_snapshot_status=chain_status,
        app_mode=str(settings.app_mode.value),
        api_degraded=api_deg_bool,
        chain_snapshot_age_sec=chain_age,
        last_quote_tick_iso=tick_iso,
        live_candidate_pipeline_enabled=pipeline,
        spy_scalper_synthetic_blocked=True,
        spy_scalper_synthetic_block_reason=SPY_SYNTHETIC_BLOCK_REASON,
    )


def build_event_edge_runtime_health(settings: Settings) -> dict[str, Any]:
    """Same keys as `SpyRuntimeHealth.as_extension_dict` for the shared dashboard shell."""
    d = SpyRuntimeHealth(
        safe_to_trade=True,
        block_reason=None,
        last_spy_quote_age_sec=None,
        last_chain_snapshot_status="n/a_not_spy_strategy",
        app_mode=str(settings.app_mode.value),
        api_degraded=None,
        chain_snapshot_age_sec=None,
        last_quote_tick_iso=None,
        live_candidate_pipeline_enabled=settings.live_candidate_pipeline_enabled,
        spy_scalper_synthetic_blocked=False,
        spy_scalper_synthetic_block_reason=None,
    ).as_extension_dict()
    d["spy_scalper_synthetic_blocked"] = None
    d["spy_scalper_synthetic_block_reason"] = None
    return d
