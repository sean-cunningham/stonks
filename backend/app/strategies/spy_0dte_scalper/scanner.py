from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import Settings
from app.core.enums import AppMode
from app.repositories.spy_scalper_repository import SpyScalperRepository
from app.repositories.strategy_bot_state_repository import SPY_SCALPER_SLUG, StrategyBotStateRepository
from app.services.market_data.quote_cache import QuoteCache
from app.strategies.spy_0dte_scalper.ai_filter import run_ai_filter_sync
from app.strategies.spy_0dte_scalper.config import effective_config
from app.strategies.spy_0dte_scalper.contract_selector import select_contract
from app.strategies.spy_0dte_scalper.features import compute_features, synthesize_bars
from app.strategies.spy_0dte_scalper.position_manager import open_paper_position
from app.strategies.spy_0dte_scalper.risk_manager import evaluate_new_entry
from app.strategies.spy_0dte_scalper.scorer import score_setup
from app.strategies.spy_0dte_scalper.live_readiness import SPY_SYNTHETIC_BLOCK_REASON, spy_underlying_mid
from app.strategies.spy_0dte_scalper.setup_detector import detect_setups
from app.strategies.spy_0dte_scalper.state import ScalperRuntimeState

log = logging.getLogger(__name__)


def _trade_day_str(now: datetime) -> str:
    return now.date().isoformat()


def run_tick(db: Session, settings: Settings, quote_cache: QuoteCache) -> None:
    strat_repo = StrategyBotStateRepository(db)
    row = strat_repo.get_or_create(SPY_SCALPER_SLUG)
    if row.state != "running":
        return
    now = utc_now()
    if row.cooldown_until and now < row.cooldown_until:
        return

    cfg = effective_config(settings, row.config_json)

    trade_day = _trade_day_str(now)
    runtime = ScalperRuntimeState.from_json(row.scalper_state_json, trade_day, cfg.deployable_target)

    spy_repo = SpyScalperRepository(db)
    open_pos = spy_repo.get_open_position()
    summary = spy_repo.get_daily_summary(trade_day)
    trades_today = int(summary.trades_count) if summary else 0
    daily_net = float(summary.net_pnl) if summary else 0.0

    if settings.app_mode != AppMode.MOCK:
        spy_repo.log_candidate(
            trade_day=trade_day,
            outcome="blocked_synthetic_execution",
            reason=SPY_SYNTHETIC_BLOCK_REASON,
            features_json={"app_mode": settings.app_mode.value},
        )
        log.info("spy scalper tick skipped: %s", SPY_SYNTHETIC_BLOCK_REASON)
        return

    mid = spy_underlying_mid(quote_cache)
    if mid is None:
        mid = 500.0
    bars = synthesize_bars(mid, n=90, seed=now.hour * 60 + now.minute)
    features = compute_features(mid, bars)

    setups = detect_setups(features)
    if not setups:
        spy_repo.log_candidate(
            trade_day=trade_day,
            outcome="no_setup",
            reason="no_pattern",
            features_json=features,
        )
        return

    best = None
    best_score = -1.0
    for s in setups:
        if s.family in runtime.disabled_families:
            continue
        sc, meta = score_setup(s, features)
        floor = float(meta["exec_floor"])
        if sc < floor:
            spy_repo.log_candidate(
                trade_day=trade_day,
                outcome="below_exec_floor",
                setup_family=s.family,
                direction=s.direction,
                base_score=sc,
                reason=f"floor={floor}",
                features_json=features,
            )
            continue
        if sc > best_score:
            best_score = sc
            best = (s, sc, meta)

    if not best:
        spy_repo.log_candidate(
            trade_day=trade_day,
            outcome="all_below_exec_floor",
            reason="no_setup_met_floor",
            features_json=features,
        )
        return

    setup, base_score, meta = best
    final_score = base_score
    ai_adj = 0.0
    verdict = None

    if base_score >= cfg.pre_ai_min_score:
        ai_adj, verdict, ai_err = run_ai_filter_sync(
            settings,
            cfg,
            setup,
            base_score,
            features,
            ai_calls_today=runtime.ai_calls_today,
        )
        if ai_err is None:
            runtime.ai_calls_today += 1
        final_score = max(0.0, min(100.0, base_score + ai_adj))
        if verdict and verdict.pass_take.upper() == "PASS":
            spy_repo.log_candidate(
                trade_day=trade_day,
                outcome="ai_pass",
                setup_family=setup.family,
                direction=setup.direction,
                base_score=base_score,
                ai_adjustment=ai_adj,
                final_score=final_score,
                reason=verdict.reason_short,
                features_json=features,
                payload_json=verdict.model_dump(),
            )
            strat_repo.update_scalper_state_json(SPY_SCALPER_SLUG, runtime.to_json())
            return

    if final_score < meta["exec_floor"]:
        spy_repo.log_candidate(
            trade_day=trade_day,
            outcome="post_ai_below_floor",
            setup_family=setup.family,
            direction=setup.direction,
            base_score=base_score,
            ai_adjustment=ai_adj,
            final_score=final_score,
            features_json=features,
        )
        strat_repo.update_scalper_state_json(SPY_SCALPER_SLUG, runtime.to_json())
        return

    risk = evaluate_new_entry(
        cfg,
        runtime,
        trades_today=trades_today,
        daily_net_pnl=daily_net,
        setup_family=setup.family,
        has_open_position=open_pos is not None,
    )
    if not risk.ok:
        spy_repo.log_candidate(
            trade_day=trade_day,
            outcome="risk_reject",
            setup_family=setup.family,
            direction=setup.direction,
            base_score=base_score,
            final_score=final_score,
            reason=risk.reason,
            features_json=features,
        )
        strat_repo.update_scalper_state_json(SPY_SCALPER_SLUG, runtime.to_json())
        return

    leg = select_contract(mid, setup.direction, cfg)
    if not leg:
        spy_repo.log_candidate(
            trade_day=trade_day,
            outcome="no_contract",
            setup_family=setup.family,
            direction=setup.direction,
            base_score=base_score,
            final_score=final_score,
            reason="selector_reject",
            features_json=features,
        )
        strat_repo.update_scalper_state_json(SPY_SCALPER_SLUG, runtime.to_json())
        return

    pos = open_paper_position(
        db,
        spy_repo,
        cfg=cfg,
        setup_family=setup.family,
        right=leg.right,
        strike=leg.strike,
        expiry=leg.expiry,
        mid=leg.mid,
    )
    cost = float(pos.entry_fill_price) * 100.0 * int(pos.quantity)
    runtime.deployable_cash = max(0.0, runtime.deployable_cash - cost)
    spy_repo.log_candidate(
        trade_day=trade_day,
        outcome="placed",
        setup_family=setup.family,
        direction=setup.direction,
        base_score=base_score,
        ai_adjustment=ai_adj,
        final_score=final_score,
        reason="paper_open",
        features_json=features,
        payload_json={"position_id": pos.id, "meta": meta},
    )
    strat_repo.update_scalper_state_json(SPY_SCALPER_SLUG, runtime.to_json())
    log.info("spy scalper opened position id=%s family=%s", pos.id, setup.family)
