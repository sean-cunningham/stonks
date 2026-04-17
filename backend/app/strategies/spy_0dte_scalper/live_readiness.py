"""Live paper readiness for SPY 0DTE scalper (non-mock modes only)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import Settings
from app.core.enums import AppMode
from app.models.market_snapshot import MarketSnapshot
from app.services.market_data.quote_cache import QuoteCache, QuoteTick

MAX_SPY_QUOTE_AGE_SEC = 120.0


@dataclass
class SpyRuntimeHealth:
    safe_to_trade: bool
    block_reason: str | None
    last_spy_quote_age_sec: float | None
    last_chain_snapshot_status: str

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


def latest_spy_snapshot_row(db: Session) -> MarketSnapshot | None:
    return db.scalars(
        select(MarketSnapshot).where(MarketSnapshot.symbol == "SPY").order_by(MarketSnapshot.id.desc()).limit(1),
    ).first()


def evaluate_spy_live_paper_readiness(
    db: Session,
    settings: Settings,
    quote_cache: QuoteCache,
) -> SpyRuntimeHealth:
    if settings.app_mode == AppMode.MOCK:
        return SpyRuntimeHealth(
            safe_to_trade=True,
            block_reason=None,
            last_spy_quote_age_sec=_quote_age_sec(quote_cache.get("SPY")),
            last_chain_snapshot_status="mock_mode",
        )

    tick = quote_cache.get("SPY")
    mid = _mid_from_tick(tick)
    q_age = _quote_age_sec(tick)
    if mid is None or mid <= 0:
        return SpyRuntimeHealth(
            safe_to_trade=False,
            block_reason="missing_spy_quote",
            last_spy_quote_age_sec=q_age,
            last_chain_snapshot_status="n/a",
        )
    if q_age is not None and q_age > MAX_SPY_QUOTE_AGE_SEC:
        return SpyRuntimeHealth(
            safe_to_trade=False,
            block_reason="stale_spy_quote",
            last_spy_quote_age_sec=q_age,
            last_chain_snapshot_status="n/a",
        )

    snap = latest_spy_snapshot_row(db)
    if not snap:
        return SpyRuntimeHealth(
            safe_to_trade=False,
            block_reason="missing_spy_snapshot",
            last_spy_quote_age_sec=q_age,
            last_chain_snapshot_status="missing",
        )
    ex = snap.extra or {}
    if ex.get("api_degraded"):
        return SpyRuntimeHealth(
            safe_to_trade=False,
            block_reason="api_degraded",
            last_spy_quote_age_sec=q_age,
            last_chain_snapshot_status="degraded",
        )
    return SpyRuntimeHealth(
        safe_to_trade=True,
        block_reason=None,
        last_spy_quote_age_sec=q_age,
        last_chain_snapshot_status="ok",
    )
