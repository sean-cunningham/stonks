from app.core.clock import utc_now
from app.models.approved_trade import ApprovedTrade
from app.models.candidate_trade import CandidateTrade
from app.models.trade_review import TradeReview
from app.services.analytics.recommendation_engine import refresh_recommendations


def _loss_review(approved_trade_id: int):
    return TradeReview(
        created_at=utc_now(),
        approved_trade_id=approved_trade_id,
        symbol="SPY",
        setup_type="bullish_post_event_confirmation",
        trade_family="confirmed",
        entry_price=1.0,
        quantity=1,
        realized_pnl_dollars=-50.0,
        realized_r_multiple=-1.0,
        exit_quality_label="adverse_stop_exit",
        mfe_dollars=30.0,
        mae_dollars=60.0,
        hit_plus_1r=False,
        hit_plus_1_5r=False,
        hit_plus_2r=False,
        had_x_enrichment=False,
        had_thenewsapi_supplement=False,
    )


def test_recommendation_engine_adds_row_when_sample_poor(db_session):
    for _ in range(6):
        c = CandidateTrade(
            created_at=utc_now(),
            symbol="SPY",
            strategy="debit_spread",
            candidate_kind="test",
            direction_bias="bullish",
            legs=[],
            setup_type="bullish_post_event_confirmation",
        )
        db_session.add(c)
        db_session.flush()
        a = ApprovedTrade(
            created_at=utc_now(),
            candidate_trade_id=c.id,
            status="filled",
        )
        db_session.add(a)
        db_session.flush()
        db_session.add(_loss_review(a.id))
    db_session.commit()

    n = refresh_recommendations(db_session)
    assert n >= 1
