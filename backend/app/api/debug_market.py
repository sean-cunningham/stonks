"""Read-only market data debug (QuoteCache + latest snapshots)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.jobs.scheduler import get_quote_cache
from app.models.market_snapshot import MarketSnapshot
from app.services.strategy.candidate_generator import DEFAULT_WATCHLIST

router = APIRouter(tags=["debug"])


@router.get("/debug/market-data")
def market_data_debug(db: Session = Depends(get_db)) -> dict:
    s = get_settings()
    if not s.market_debug_endpoint_enabled and s.app_env.lower() != "development":
        raise HTTPException(status_code=404, detail="not found")

    qc = get_quote_cache()
    quotes: dict[str, dict] = {}
    for sym, tick in qc.snapshot().items():
        quotes[sym] = {
            "bid": tick.bid,
            "ask": tick.ask,
            "last": tick.last,
            "volume": tick.volume,
        }

    snapshots: dict[str, dict] = {}
    for sym in DEFAULT_WATCHLIST:
        row = db.scalar(
            select(MarketSnapshot)
            .where(MarketSnapshot.symbol == sym)
            .order_by(desc(MarketSnapshot.created_at))
            .limit(1)
        )
        if row:
            ex = row.extra or {}
            snapshots[sym] = {
                "id": row.id,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "underlying_price": row.underlying_price,
                "bid": row.bid,
                "ask": row.ask,
                "quote_ts_epoch": ex.get("quote_ts_epoch"),
                "chain_ts_epoch": ex.get("chain_ts_epoch"),
                "chain_error": ex.get("chain_error"),
                "api_degraded": ex.get("api_degraded"),
                "strike_count": (ex.get("chain_liquidity") or {}).get("strike_count"),
            }

    return {"quotes": quotes, "latest_snapshots": snapshots}
