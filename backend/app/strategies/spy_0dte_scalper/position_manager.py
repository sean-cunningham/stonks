from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.spy_scalper_fill import SpyScalperFill
from app.models.spy_scalper_position import SpyScalperPosition
from app.repositories.spy_scalper_repository import SpyScalperRepository
from app.strategies.spy_0dte_scalper.config import ScalperEffectiveConfig
from app.strategies.spy_0dte_scalper.execution import paper_limit_fill_buy


def open_paper_position(
    db: Session,
    repo: SpyScalperRepository,
    *,
    cfg: ScalperEffectiveConfig,
    setup_family: str,
    right: str,
    strike: float,
    expiry: str,
    mid: float,
) -> SpyScalperPosition:
    fill_px = paper_limit_fill_buy(mid, cfg)
    now = utc_now()
    pos = SpyScalperPosition(
        symbol="SPY",
        status="open",
        right=right,
        strike=strike,
        expiry=expiry,
        quantity=1,
        entry_mid=mid,
        entry_fill_price=fill_px,
        exit_fill_price=None,
        current_mark=fill_px,
        unrealized_pnl=0.0,
        realized_pnl=None,
        setup_family=setup_family,
        high_water_mark=fill_px,
        low_water_mark=fill_px,
        take_profit_price=fill_px * (1.0 + cfg.tp_pct),
        stop_price=fill_px * (1.0 - cfg.stop_pct),
        max_hold_until=now + timedelta(minutes=cfg.max_hold_minutes),
        fast_fail_until=now + timedelta(minutes=cfg.fast_fail_minutes),
        opened_at=now,
        closed_at=None,
        close_reason=None,
    )
    repo.open_position(pos)
    repo.add_fill(
        SpyScalperFill(
            position_id=pos.id,
            side="buy",
            quantity=1,
            price=fill_px,
            filled_at=now,
        )
    )
    return pos
