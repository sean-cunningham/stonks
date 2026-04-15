from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.event_analysis import EventAnalysis

WIDE_EVENTS = {"macro_announcement", "fed", "powell", "cpi", "nfp"}


def is_event_lockout_active(db: Session) -> bool:
    now = utc_now()
    recent = list(
        db.scalars(
            select(EventAnalysis)
            .order_by(EventAnalysis.created_at.desc())
            .limit(20),
        ).all()
    )
    for ev in recent:
        kind = (ev.event_type or "").lower()
        if kind in WIDE_EVENTS:
            if abs((now - ev.created_at).total_seconds()) <= 30 * 60:
                return True
        else:
            if abs((now - ev.created_at).total_seconds()) <= 15 * 60:
                return True
    return False
