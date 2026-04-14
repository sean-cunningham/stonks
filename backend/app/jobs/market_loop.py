import logging
import random

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import Settings
from app.core.enums import AppMode
from app.models.approved_trade import ApprovedTrade
from app.models.market_snapshot import MarketSnapshot
from app.repositories.bot_state_repository import BotStateRepository
from app.repositories.candidate_repository import CandidateRepository
from app.services.execution.paper_broker import PaperBroker
from app.services.market_data.quote_cache import QuoteCache, QuoteTick
from app.services.policy.approval_engine import ApprovalEngine
from app.services.strategy.candidate_generator import DEFAULT_WATCHLIST, maybe_build_candidate

log = logging.getLogger(__name__)


def _mock_snapshot_for_symbol(db: Session, symbol: str) -> MarketSnapshot:
    base = 100 + hash(symbol) % 400 + random.random() * 3
    bid, ask = base - 0.02, base + 0.02
    snap = MarketSnapshot(
        symbol=symbol,
        created_at=utc_now(),
        underlying_price=(bid + ask) / 2,
        bid=bid,
        ask=ask,
        volume=800_000,
        spread_bps=2.0,
        extra={"chain_liquidity": {"strike_count": 40.0}, "mock": True},
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


def run_market_tick(db: Session, settings: Settings, quote_cache: QuoteCache) -> None:
    bot = BotStateRepository(db).get()
    if bot.state != "running":
        return
    if settings.app_mode == AppMode.MOCK:
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
            notes=spec.notes,
        )
        eng = ApprovalEngine(db, settings)
        outcome, tid = eng.try_approve(cand.id)
        if outcome != "approved" or not tid:
            log.info("approval rejected id=%s", tid)
            return
        appr = db.get(ApprovedTrade, tid)
        if not appr:
            return
        pb = PaperBroker(db, settings)
        pb.execute_approved_open(appr, bid=snap.bid, ask=snap.ask, mid=snap.underlying_price)
        return
