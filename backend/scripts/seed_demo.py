"""Seed demo rows for mock dashboard (run from backend/: python -m scripts.seed_demo)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.models import Base
from app.models.account import Account
from app.models.bot_state import BotStateRow
from app.models.candidate_trade import CandidateTrade
from app.models.event_analysis import EventAnalysis
from app.models.market_snapshot import MarketSnapshot
from app.models.rejected_trade import RejectedTrade


def seed(db: Session) -> None:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)

    acc = db.get(Account, 1)
    if not acc:
        acc = Account(
            id=1,
            cash_balance=settings.bot_default_starting_cash,
            equity=settings.bot_default_starting_cash,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            currency="USD",
            updated_at=utc_now(),
        )
        db.add(acc)
    bot = db.get(BotStateRow, 1)
    if not bot:
        db.add(
            BotStateRow(
                id=1,
                state="stopped",
                pause_reason=None,
                cooldown_until=None,
                updated_at=utc_now(),
            ),
        )

    snap_count = db.scalar(select(func.count()).select_from(MarketSnapshot)) or 0
    if snap_count == 0:
        snap = MarketSnapshot(
            symbol="SPY",
            created_at=utc_now(),
            underlying_price=512.34,
            bid=512.30,
            ask=512.38,
            volume=1_200_000,
            spread_bps=1.5,
            extra={"regime": "trend_up"},
        )
        db.add(snap)
        db.flush()
        ev = EventAnalysis(
            created_at=utc_now(),
            symbol="SPY",
            normalized_event_id="demo-earnings-1",
            event_type="earnings",
            materiality_score=72,
            surprise_score=55,
            direction_bias="bullish",
            confidence_score=68,
            time_horizon="intraday",
            priced_in_risk="medium",
            narrative_summary="EPS beat consensus on stronger cloud growth. Guidance was unchanged but tone was constructive.",
            key_evidence_points=["EPS beat", "Revenue inline", "Margins stable"],
            tradeability_flag=True,
            recommended_strategy="debit_spread",
            raw_response_json=None,
            validation_ok=True,
        )
        db.add(ev)
        db.flush()
        c = CandidateTrade(
            created_at=utc_now(),
            market_snapshot_id=snap.id,
            symbol="SPY",
            strategy="debit_spread",
            candidate_kind="bullish_continuation",
            direction_bias="long",
            legs=[
                {"action": "buy", "strike": 510, "right": "C", "expiry": "2026-05-16"},
                {"action": "sell", "strike": 515, "right": "C", "expiry": "2026-05-16"},
            ],
            is_event_driven=True,
            event_analysis_id=ev.id,
            metadata_json={"dte": 33},
            notes="Demo candidate from seed script.",
        )
        db.add(c)
        db.flush()
        db.add(
            RejectedTrade(
                created_at=utc_now(),
                candidate_trade_id=c.id,
                event_analysis_id=ev.id,
                reasons=["Spread 8.2% of mid exceeds 5% threshold in mock demo."],
                rule_codes=["LIQUIDITY_SPREAD"],
                detail="Deterministic demo rejection.",
            ),
        )
    db.commit()
    print("Seed complete.")


def main() -> None:
    load = __import__("dotenv", fromlist=["load_dotenv"]).load_dotenv
    load()
    session = SessionLocal()
    try:
        seed(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()
