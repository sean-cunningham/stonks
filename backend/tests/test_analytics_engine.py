from app.core.clock import utc_now
from app.models.approved_trade import ApprovedTrade
from app.models.candidate_trade import CandidateTrade
from app.models.trade_review import TradeReview
from app.services.analytics.analytics_engine import summarize_by_setup, summarize_global


def _review(db, *, pnl: float, setup: str | None = "bullish_post_event_confirmation", **kw):
    c = CandidateTrade(
        created_at=utc_now(),
        symbol="SPY",
        strategy="debit_spread",
        candidate_kind="test",
        direction_bias="bullish",
        legs=[],
        setup_type=setup,
    )
    db.add(c)
    db.flush()
    a = ApprovedTrade(
        created_at=utc_now(),
        candidate_trade_id=c.id,
        status="filled",
    )
    db.add(a)
    db.flush()
    row = TradeReview(
        created_at=utc_now(),
        approved_trade_id=a.id,
        candidate_trade_id=c.id,
        symbol="SPY",
        setup_type=setup,
        trade_family="anticipatory" if setup == "anticipatory_macro_event" else "confirmed",
        entry_price=1.0,
        exit_price=1.1,
        exit_reason="trailing_stop_hit",
        quantity=1,
        realized_pnl_dollars=pnl,
        realized_r_multiple=pnl / 50.0 if pnl else 0.0,
        mfe_dollars=abs(pnl) + 1.0,
        mae_dollars=1.0,
        holding_seconds=60,
        hit_plus_1r=pnl > 0,
        hit_plus_1_5r=False,
        hit_plus_2r=False,
        exit_quality_label="structured_win_exit" if pnl > 0 else "adverse_stop_exit",
        **kw,
    )
    db.add(row)
    db.commit()


def test_summarize_global_expectancy(db_session):
    _review(db_session, pnl=50.0)
    _review(db_session, pnl=-20.0)
    from app.services.analytics.analytics_engine import load_all_reviews

    rows = load_all_reviews(db_session)
    g = summarize_global(rows)
    assert g["trade_count"] == 2
    assert abs(g["expectancy"] - 15.0) < 1e-6


def test_summarize_by_setup_groups(db_session):
    _review(db_session, pnl=10.0, setup="bullish_post_event_confirmation")
    _review(db_session, pnl=-5.0, setup="bearish_post_event_confirmation")
    from app.services.analytics.analytics_engine import load_all_reviews

    rows = load_all_reviews(db_session)
    slices = summarize_by_setup(rows)
    kinds = {s["setup_type"] for s in slices}
    assert "bullish_post_event_confirmation" in kinds
    assert "bearish_post_event_confirmation" in kinds
