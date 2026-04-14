from app.core.clock import utc_now
from app.models.approved_trade import ApprovedTrade
from app.models.candidate_trade import CandidateTrade
from app.models.trade_review import TradeReview
from app.repositories.parameter_experiment_repository import ParameterExperimentRepository
from app.services.analytics.shadow_experiments import run_shadow_experiments_for_review
from app.core.config import get_settings


def test_shadow_experiments_persist(db_session):
    c = CandidateTrade(
        created_at=utc_now(),
        symbol="SPY",
        strategy="debit_spread",
        candidate_kind="test",
        direction_bias="bullish",
        legs=[],
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
    tr = TradeReview(
        created_at=utc_now(),
        approved_trade_id=a.id,
        symbol="SPY",
        trade_family="confirmed",
        entry_price=1.0,
        quantity=1,
        realized_pnl_dollars=-10.0,
        realized_r_multiple=-0.5,
    )
    db_session.add(tr)
    db_session.commit()
    db_session.refresh(tr)
    run_shadow_experiments_for_review(db_session, tr, settings=get_settings())
    repo = ParameterExperimentRepository(db_session)
    rows = repo.list_for_review(tr.id)
    assert len(rows) >= 1
    names = {r.experiment_name for r in rows}
    assert "wider_initial_stop_20pct" in names
