from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import Settings
from app.core.enums import AppMode
from app.models.spy_scalper_fill import SpyScalperFill
from app.repositories.spy_scalper_repository import SpyScalperRepository
from app.repositories.strategy_bot_state_repository import SPY_SCALPER_SLUG, StrategyBotStateRepository
from app.services.market_data.quote_cache import QuoteCache
from app.strategies.spy_0dte_scalper.config import effective_config
from app.strategies.spy_0dte_scalper.execution import paper_limit_fill_sell
from app.strategies.spy_0dte_scalper.state import ScalperRuntimeState

log = logging.getLogger(__name__)

_BASELINE_SPY = 500.0


def _underlying_mid(quote_cache: QuoteCache) -> float:
    t = quote_cache.get("SPY")
    if not t:
        return _BASELINE_SPY
    if t.bid and t.ask and t.bid > 0 and t.ask > 0:
        return (t.bid + t.ask) / 2
    if t.last and t.last > 0:
        return float(t.last)
    return _BASELINE_SPY


def _trade_day_str(now) -> str:
    return now.date().isoformat()


def run_spy_scalper_reconciliation_tick(
    db: Session,
    settings: Settings,
    quote_cache: QuoteCache,
) -> None:
    if settings.app_mode != AppMode.MOCK:
        log.info("spy scalper reconciliation skipped: live paper requires real marks (APP_MODE != mock)")
        return
    strat_repo = StrategyBotStateRepository(db)
    row = strat_repo.get_or_create(SPY_SCALPER_SLUG)
    if row.state != "running":
        return

    cfg = effective_config(settings, row.config_json)
    spy_repo = SpyScalperRepository(db)
    now = utc_now()
    trade_day = _trade_day_str(now)
    runtime = ScalperRuntimeState.from_json(
        row.scalper_state_json,
        trade_day,
        cfg.deployable_target,
    )

    spy_mid = _underlying_mid(quote_cache)
    move = (spy_mid - _BASELINE_SPY) / _BASELINE_SPY

    for pos in spy_repo.list_open_positions():
        sign = 1.0 if pos.right == "C" else -1.0
        mark = max(0.01, float(pos.entry_fill_price) * (1.0 + 0.65 * move * sign))
        pos.current_mark = mark
        qty = int(pos.quantity)
        pos.unrealized_pnl = (mark - float(pos.entry_fill_price)) * 100.0 * qty
        if pos.high_water_mark is None:
            pos.high_water_mark = mark
        if pos.low_water_mark is None:
            pos.low_water_mark = mark
        pos.high_water_mark = max(float(pos.high_water_mark), mark)
        pos.low_water_mark = min(float(pos.low_water_mark), mark)

        exit_reason: str | None = None
        if pos.take_profit_price and mark >= float(pos.take_profit_price):
            exit_reason = "take_profit"
        elif pos.stop_price and mark <= float(pos.stop_price):
            exit_reason = "stop"
        elif pos.max_hold_until and now >= pos.max_hold_until:
            exit_reason = "time_stop"
        elif pos.fast_fail_until and now >= pos.fast_fail_until and mark < float(pos.entry_fill_price) * 0.98:
            exit_reason = "fast_fail"

        if not exit_reason:
            continue

        exit_px = paper_limit_fill_sell(mark, cfg)
        realized = (exit_px - float(pos.entry_fill_price)) * 100.0 * qty
        pos.status = "closed"
        pos.closed_at = now
        pos.close_reason = exit_reason
        pos.exit_fill_price = exit_px
        pos.realized_pnl = realized
        db.flush()

        spy_repo.add_fill(
            SpyScalperFill(
                position_id=int(pos.id),
                side="sell",
                quantity=qty,
                price=exit_px,
                filled_at=now,
            ),
            commit=False,
        )

        win = realized > 0
        spy_repo.upsert_daily_summary(
            trade_day,
            net_delta=realized,
            trade_closed=True,
            win=win,
            family=pos.setup_family,
            commit=False,
        )

        runtime.deployable_cash = max(0.0, runtime.deployable_cash + exit_px * 100.0 * qty)
        if realized < 0:
            runtime.consecutive_losses += 1
            if runtime.consecutive_losses >= 2 and pos.setup_family:
                fam = set(runtime.disabled_families)
                fam.add(str(pos.setup_family))
                runtime.disabled_families = sorted(fam)
        else:
            runtime.consecutive_losses = 0

        fast_loser = exit_reason == "fast_fail" and realized < 0
        runtime.last_exit_was_fast_loser = fast_loser
        cool = (
            cfg.cooldown_after_fast_loser_seconds
            if fast_loser
            else cfg.cooldown_after_exit_seconds
        )
        strat_repo.set_cooldown(SPY_SCALPER_SLUG, now + timedelta(seconds=int(cool)), commit=False)
        strat_repo.update_scalper_state_json(SPY_SCALPER_SLUG, runtime.to_json(), commit=False)
        log.info("spy scalper closed id=%s reason=%s pnl=%s", pos.id, exit_reason, realized)

    db.commit()
