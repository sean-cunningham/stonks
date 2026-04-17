from sqlalchemy import select

from app.core.clock import utc_now
from app.core.config import get_settings
from app.models.approved_trade import ApprovedTrade
from app.models.candidate_trade import CandidateTrade
from app.models.fill import Fill
from app.services.execution.paper_broker import PaperBroker


def _valid_option_contract():
    return {"dte": 10, "delta": 0.58, "spread_abs": 0.04, "mid": 2.5}


def test_paper_open_fill_price_tracks_option_mid_not_underlying_nbbo(db_session):
    settings = get_settings()
    cand = CandidateTrade(
        created_at=utc_now(),
        symbol="SPY",
        strategy="long_call",
        candidate_kind="test",
        direction_bias="long",
        legs=[{"symbol": "SPY", "action": "buy", "strike": 500, "right": "C"}],
        metadata_json={"option_contract": _valid_option_contract()},
    )
    db_session.add(cand)
    db_session.flush()
    appr = ApprovedTrade(
        created_at=utc_now(),
        candidate_trade_id=cand.id,
        status="pending",
        risk_snapshot={},
        policy_trace={},
    )
    db_session.add(appr)
    db_session.commit()
    db_session.refresh(appr)

    pb = PaperBroker(db_session, settings)
    # Sanity reference only; fill must still come from option_contract.mid, not share price.
    pos_id = pb.execute_approved_open(appr, reference_underlying=500.0)
    assert pos_id is not None
    fl = db_session.scalars(select(Fill).where(Fill.active_position_id == pos_id)).one()
    assert fl.price < 50.0
    assert 2.0 < fl.price < 4.0


def test_paper_open_fill_ignores_absurd_reference_underlying_when_option_mid_valid(db_session):
    """Fill price is driven by option_contract; reference_underlying is only an upper sanity bound."""
    settings = get_settings()
    cand = CandidateTrade(
        created_at=utc_now(),
        symbol="SPY",
        strategy="long_call",
        candidate_kind="test",
        direction_bias="long",
        legs=[{"symbol": "SPY", "action": "buy", "strike": 500, "right": "C"}],
        metadata_json={"option_contract": _valid_option_contract()},
    )
    db_session.add(cand)
    db_session.flush()
    appr = ApprovedTrade(
        created_at=utc_now(),
        candidate_trade_id=cand.id,
        status="pending",
        risk_snapshot={},
        policy_trace={},
    )
    db_session.add(appr)
    db_session.commit()
    db_session.refresh(appr)
    pb = PaperBroker(db_session, settings)
    pos_id = pb.execute_approved_open(appr, reference_underlying=10.0)
    assert pos_id is not None
    fl = db_session.scalars(select(Fill).where(Fill.active_position_id == pos_id)).one()
    assert 2.0 < fl.price < 4.0


def test_paper_open_rejects_when_option_mid_implausible_vs_underlying(db_session):
    settings = get_settings()
    bad_contract = {**_valid_option_contract(), "mid": 400.0}
    cand = CandidateTrade(
        created_at=utc_now(),
        symbol="SPY",
        strategy="long_call",
        candidate_kind="test",
        direction_bias="long",
        legs=[{"symbol": "SPY", "action": "buy", "strike": 500, "right": "C"}],
        metadata_json={"option_contract": bad_contract},
    )
    db_session.add(cand)
    db_session.flush()
    appr = ApprovedTrade(
        created_at=utc_now(),
        candidate_trade_id=cand.id,
        status="pending",
        risk_snapshot={},
        policy_trace={},
    )
    db_session.add(appr)
    db_session.commit()
    db_session.refresh(appr)

    pb = PaperBroker(db_session, settings)
    pos_id = pb.execute_approved_open(appr, reference_underlying=500.0)
    assert pos_id is None
