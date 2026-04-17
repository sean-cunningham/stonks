from datetime import datetime, timedelta, timezone

from app.core.clock import utc_now
from app.models.event_analysis import EventAnalysis
from app.services.events.macro_lockout_service import _as_utc_aware, is_event_lockout_active


def test_as_utc_aware_naive_assumes_utc():
    naive = datetime(2026, 1, 15, 12, 0, 0)
    got = _as_utc_aware(naive)
    assert got.tzinfo == timezone.utc
    assert got.replace(tzinfo=None) == naive


def test_as_utc_aware_offset_aware_preserved():
    aware = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    assert _as_utc_aware(aware) == aware


def test_is_event_lockout_active_accepts_naive_created_at(db_session):
    """SQLite can return naive datetimes; subtracting from aware utc_now() must not raise."""
    now = utc_now()
    created = (now - timedelta(minutes=5)).replace(tzinfo=None)
    row = EventAnalysis(
        created_at=created,
        symbol="SPY",
        normalized_event_id="naive-lockout-test",
        event_source_tier="official",
        event_type="headline",
        materiality_score=50,
        surprise_score=0,
        direction_bias="neutral",
        confidence_score=50,
        time_horizon="intraday",
        priced_in_risk="medium",
        narrative_summary="test",
        key_evidence_points=[],
        tradeability_flag=True,
        recommended_strategy="none",
    )
    db_session.add(row)
    db_session.commit()
    out = is_event_lockout_active(db_session)
    assert isinstance(out, bool)
