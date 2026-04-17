import asyncio
import logging
import random
import time
from math import isfinite

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import Settings
from app.core.enums import AppMode
from app.models.approved_trade import ApprovedTrade
from app.models.market_snapshot import MarketSnapshot
from app.repositories.bot_state_repository import BotStateRepository
from app.repositories.candidate_repository import CandidateRepository
from app.services.execution.paper_broker import PaperBroker
from app.services.events.macro_lockout_service import is_event_lockout_active
from app.services.market_data.market_snapshot_service import MarketSnapshotService
from app.services.market_data.option_chain_service import OptionChainService
from app.services.market_data.quote_cache import QuoteCache, QuoteTick
from app.services.market_data.tastytrade_broker import TastytradeBrokerAdapter
from app.services.market_data.token_manager import TokenManager
from app.services.policy.approval_engine import ApprovalEngine
from app.services.strategy.candidate_generator import DEFAULT_WATCHLIST, maybe_build_candidate

log = logging.getLogger(__name__)

_LIVE_SNAPSHOT_MAX_AGE_SEC = 600.0


def _has_option_premium_for_pipeline(extra: dict) -> bool:
    oc = extra.get("option_contract") or {}
    if not isinstance(oc, dict):
        return False
    for k in ("spread_mid", "mid"):
        v = oc.get(k)
        if v is None:
            continue
        try:
            f = float(v)
            if isfinite(f) and f > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _snapshot_freshness_ok(extra: dict, *, max_age_sec: float = _LIVE_SNAPSHOT_MAX_AGE_SEC) -> bool:
    now = time.time()
    for key in ("quote_ts_epoch", "chain_ts_epoch"):
        ts = extra.get(key)
        if ts is None:
            return False
        try:
            if now - float(ts) > max_age_sec:
                return False
        except (TypeError, ValueError):
            return False
    return True


def _try_live_candidate_pipeline(db: Session, settings: Settings, snap: MarketSnapshot) -> None:
    extra = snap.extra or {}
    if not _has_option_premium_for_pipeline(extra):
        log.info("live candidate pipeline skip symbol=%s reason=no_option_contract", snap.symbol)
        return
    if not _snapshot_freshness_ok(extra):
        log.info("live candidate pipeline skip symbol=%s reason=stale_snapshot_fields", snap.symbol)
        return
    spec, reason = maybe_build_candidate(
        snap,
        settings=settings,
        event_type="headline",
        event_id=f"live-tick-{snap.symbol}",
        direction_bias="bullish",
        materiality_score=70,
        confidence_score=65,
        event_mixed=False,
        anticipatory_allowed=False,
    )
    if not spec:
        log.info("live candidate pipeline symbol=%s no_candidate reason=%s", snap.symbol, reason)
        return
    cr = CandidateRepository(db)
    cand = cr.create(
        symbol=spec.symbol,
        strategy=spec.strategy.value,
        candidate_kind=spec.candidate_kind,
        setup_type=spec.setup_type,
        setup_score=spec.setup_score,
        reason_codes=spec.reason_codes,
        confirmation_state=spec.confirmation_state,
        event_id=spec.event_id,
        direction_bias=spec.direction_bias,
        legs=spec.legs,
        market_snapshot_id=snap.id,
        is_event_driven=spec.is_event_driven,
        metadata={"option_contract": (snap.extra or {}).get("option_contract", {})},
        notes=spec.notes,
    )
    eng = ApprovalEngine(db, settings)
    outcome, tid = eng.try_approve(cand.id)
    if outcome == "recommend_only":
        log.info("live candidate pipeline recommend-only id=%s symbol=%s", tid, snap.symbol)
        return
    if outcome != "approved" or not tid:
        log.info("live candidate pipeline approval not approved outcome=%s id=%s symbol=%s", outcome, tid, snap.symbol)
        return
    appr = db.get(ApprovedTrade, tid)
    if not appr:
        return
    pb = PaperBroker(db, settings)
    pb.execute_approved_open(
        appr,
        bid=snap.bid,
        ask=snap.ask,
        mid=snap.underlying_price,
        reference_underlying=snap.underlying_price,
    )
    log.info("live candidate pipeline filled approved id=%s symbol=%s", tid, snap.symbol)


def _mock_snapshot_for_symbol(db: Session, symbol: str) -> MarketSnapshot:
    base = 100 + hash(symbol) % 400 + random.random() * 3
    bid, ask = base - 0.02, base + 0.02
    bars_1m = []
    px = base - 0.8
    for i in range(30):
        drift = 0.04 if i % 3 != 0 else -0.01
        o = px
        c = px + drift
        h = max(o, c) + 0.03
        l = min(o, c) - 0.02
        bars_1m.append({"open": o, "high": h, "low": l, "close": c, "volume": 1200 + i * 5})
        px = c
    bars_5m = []
    px5 = base - 1.2
    for i in range(18):
        drift = 0.18 if i % 5 != 0 else -0.05
        o = px5
        c = px5 + drift
        h = max(o, c) + 0.08
        l = min(o, c) - 0.06
        bars_5m.append({"open": o, "high": h, "low": l, "close": c, "volume": 7200 + i * 90})
        px5 = c
    bars_15m = []
    px15 = base - 1.6
    for i in range(8):
        drift = 0.28 if i % 4 != 0 else -0.06
        o = px15
        c = px15 + drift
        bars_15m.append({"open": o, "high": max(o, c) + 0.10, "low": min(o, c) - 0.09, "close": c, "volume": 21000 + i * 120})
        px15 = c
    now_epoch = utc_now().timestamp()
    snap = MarketSnapshot(
        symbol=symbol,
        created_at=utc_now(),
        underlying_price=(bid + ask) / 2,
        bid=bid,
        ask=ask,
        volume=800_000,
        spread_bps=2.0,
        extra={
            "chain_liquidity": {"strike_count": 40.0},
            "mock": True,
            "bars_1m": bars_1m,
            "bars_5m": bars_5m,
            "bars_15m": bars_15m,
            "prev_day_high": base + 3.0,
            "prev_day_low": base - 3.0,
            "premarket_high": base + 1.3,
            "premarket_low": base - 1.1,
            "opening_range_high": base + 0.5,
            "opening_range_low": base - 0.6,
            "quote_ts_epoch": now_epoch,
            "chain_ts_epoch": now_epoch,
            "api_degraded": False,
            "event_lockout_active": is_event_lockout_active(db),
            "major_news_block_active": False,
            "inside_opening_range_after_1015": False,
            "option_contract": {
                "dte": 10,
                "delta": 0.58,
                "spread_abs": 0.04,
                "mid": 1.2,
                "chain_activity_score": 0.8,
                "single_leg_exceeds_risk": False,
                "iv_rich": True,
                "move_not_explosive": True,
                "spread_improves_fit": True,
                "spread_mid": 1.35,
                "spread_bid_ask": 0.08,
                "spread_max_reward": 180,
                "spread_max_risk": 130,
            },
        },
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


async def _persist_live_snapshots_async(
    db: Session,
    settings: Settings,
    quote_cache: QuoteCache,
    token_manager: TokenManager,
) -> None:
    broker = TastytradeBrokerAdapter(settings, token_manager)
    ocs = OptionChainService(broker)
    mss = MarketSnapshotService(db, quote_cache, ocs)
    pipeline_note = (
        "live_candidate_pipeline_enabled"
        if settings.live_candidate_pipeline_enabled
        else "live_candidate_pipeline_disabled_default"
    )
    for sym in DEFAULT_WATCHLIST:
        snap = await mss.build_and_persist(sym)
        ex = snap.extra or {}
        liq = ex.get("chain_liquidity") or {}
        tick = quote_cache.get(sym)
        quote_present = bool(tick and ((tick.bid and tick.ask) or tick.last))
        strike_count = liq.get("strike_count")
        log.info(
            "live market tick symbol=%s quote_present=%s chain_strike_count=%s "
            "quote_ts_epoch=%s chain_ts_epoch=%s api_degraded=%s option_contract_ok=%s downstream=%s",
            sym,
            quote_present,
            strike_count,
            ex.get("quote_ts_epoch"),
            ex.get("chain_ts_epoch"),
            ex.get("api_degraded"),
            _has_option_premium_for_pipeline(ex),
            pipeline_note,
        )
        if settings.live_candidate_pipeline_enabled:
            _try_live_candidate_pipeline(db, settings, snap)


def run_live_market_snapshots(
    db: Session,
    settings: Settings,
    quote_cache: QuoteCache,
    token_manager: TokenManager,
) -> None:
    if settings.app_mode == AppMode.MOCK:
        return
    try:
        asyncio.run(_persist_live_snapshots_async(db, settings, quote_cache, token_manager))
    except Exception:
        log.exception("live market snapshot tick failed")


def run_market_tick(
    db: Session,
    settings: Settings,
    quote_cache: QuoteCache,
    token_manager: TokenManager | None = None,
) -> None:
    bot = BotStateRepository(db).get()
    if bot.state != "running":
        log.info("market_tick skipped: bot state=%s (Strategy 1 live/mock pipeline inactive)", bot.state)
        return
    if settings.app_mode == AppMode.MOCK:
        log.info("market_tick branch=mock")
        sym = random.choice(DEFAULT_WATCHLIST)
        mid = 200 + random.random() * 50
        bid, ask = mid - 0.05, mid + 0.05
        quote_cache.update(
            QuoteTick(symbol=sym, bid=bid, ask=ask, last=mid, volume=1e6),
        )
        snap = _mock_snapshot_for_symbol(db, sym)
        spec, reason = maybe_build_candidate(
            snap,
            settings=settings,
            event_type="headline",
            event_id=f"mock-{sym}",
            direction_bias="bullish" if random.random() > 0.5 else "bearish",
            materiality_score=70,
            confidence_score=65,
            event_mixed=False,
            anticipatory_allowed=False,
        )
        if not spec:
            log.debug("no candidate: %s", reason)
            return
        cr = CandidateRepository(db)
        cand = cr.create(
            symbol=spec.symbol,
            strategy=spec.strategy.value,
            candidate_kind=spec.candidate_kind,
            setup_type=spec.setup_type,
            setup_score=spec.setup_score,
            reason_codes=spec.reason_codes,
            confirmation_state=spec.confirmation_state,
            event_id=spec.event_id,
            direction_bias=spec.direction_bias,
            legs=spec.legs,
            market_snapshot_id=snap.id,
            is_event_driven=spec.is_event_driven,
            metadata={"option_contract": (snap.extra or {}).get("option_contract", {})},
            notes=spec.notes,
        )
        eng = ApprovalEngine(db, settings)
        outcome, tid = eng.try_approve(cand.id)
        if outcome == "recommend_only":
            log.info("recommend-only emitted id=%s", tid)
            return
        if outcome != "approved" or not tid:
            log.info("approval rejected id=%s", tid)
            return
        appr = db.get(ApprovedTrade, tid)
        if not appr:
            return
        pb = PaperBroker(db, settings)
        pb.execute_approved_open(
            appr,
            bid=snap.bid,
            ask=snap.ask,
            mid=snap.underlying_price,
            reference_underlying=snap.underlying_price,
        )
        return

    log.info("market_tick branch=live app_mode=%s", settings.app_mode.value)
    if token_manager is None:
        log.info(
            "live snapshot tick skipped: no token_manager (snapshots only when scheduler wires broker); "
            "Strategy 1 candidate/approval/paper path did not run this tick",
        )
        return
    run_live_market_snapshots(db, settings, quote_cache, token_manager)
    if not settings.live_candidate_pipeline_enabled:
        log.info(
            "Strategy 1 post-snapshot: candidate/approval/paper pipeline not run "
            "(LIVE_CANDIDATE_PIPELINE_ENABLED=false); snapshots were persisted if snapshot job succeeded",
        )
