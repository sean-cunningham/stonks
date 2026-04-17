from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.event_analysis import EventAnalysis

WIDE_EVENTS = {"macro_announcement", "fed", "powell", "cpi", "nfp"}


def _as_utc_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


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
        created = _as_utc_aware(ev.created_at)
        if kind in WIDE_EVENTS:
            if abs((now - created).total_seconds()) <= 30 * 60:
                return True
        else:
            if abs((now - created).total_seconds()) <= 15 * 60:
                return True
    return False
