from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.spy_scalper_candidate_event import SpyScalperCandidateEvent
from app.models.spy_scalper_daily_summary import SpyScalperDailySummary
from app.models.spy_scalper_fill import SpyScalperFill
from app.models.spy_scalper_position import SpyScalperPosition


class SpyScalperRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def log_candidate(
        self,
        *,
        trade_day: str,
        outcome: str,
        setup_family: str | None = None,
        direction: str | None = None,
        base_score: float | None = None,
        ai_adjustment: float | None = None,
        final_score: float | None = None,
        reason: str | None = None,
        features_json: dict | None = None,
        payload_json: dict | None = None,
        commit: bool = True,
    ) -> SpyScalperCandidateEvent:
        row = SpyScalperCandidateEvent(
            created_at=utc_now(),
            trade_day=trade_day,
            outcome=outcome,
            setup_family=setup_family,
            direction=direction,
            base_score=base_score,
            ai_adjustment=ai_adjustment,
            final_score=final_score,
            reason=reason,
            features_json=features_json,
            payload_json=payload_json,
        )
        self._db.add(row)
        if commit:
            self._db.commit()
            self._db.refresh(row)
        else:
            self._db.flush()
            self._db.refresh(row)
        return row

    def open_position(self, pos: SpyScalperPosition, *, commit: bool = True) -> SpyScalperPosition:
        self._db.add(pos)
        if commit:
            self._db.commit()
            self._db.refresh(pos)
        else:
            self._db.flush()
            self._db.refresh(pos)
        return pos

    def add_fill(self, fill: SpyScalperFill, *, commit: bool = True) -> SpyScalperFill:
        self._db.add(fill)
        if commit:
            self._db.commit()
            self._db.refresh(fill)
        else:
            self._db.flush()
            self._db.refresh(fill)
        return fill

    def get_open_position(self) -> SpyScalperPosition | None:
        return self._db.scalar(
            select(SpyScalperPosition).where(SpyScalperPosition.status == "open").limit(1)
        )

    def get_position(self, position_id: int) -> SpyScalperPosition | None:
        return self._db.get(SpyScalperPosition, position_id)

    def list_open_positions(self) -> list[SpyScalperPosition]:
        return list(self._db.scalars(select(SpyScalperPosition).where(SpyScalperPosition.status == "open")).all())

    def recent_candidates(self, limit: int = 50) -> list[SpyScalperCandidateEvent]:
        q = select(SpyScalperCandidateEvent).order_by(desc(SpyScalperCandidateEvent.created_at)).limit(limit)
        return list(self._db.scalars(q).all())

    def recent_closed_positions(self, limit: int = 30) -> list[SpyScalperPosition]:
        q = (
            select(SpyScalperPosition)
            .where(SpyScalperPosition.status == "closed")
            .order_by(desc(SpyScalperPosition.closed_at))
            .limit(limit)
        )
        return list(self._db.scalars(q).all())

    def upsert_daily_summary(
        self,
        summary_date: str,
        *,
        net_delta: float = 0.0,
        trade_closed: bool = False,
        win: bool | None = None,
        family: str | None = None,
        commit: bool = True,
    ) -> SpyScalperDailySummary:
        row = self._db.scalar(select(SpyScalperDailySummary).where(SpyScalperDailySummary.summary_date == summary_date))
        now = utc_now()
        if not row:
            row = SpyScalperDailySummary(
                summary_date=summary_date,
                net_pnl=0.0,
                trades_count=0,
                wins=0,
                losses=0,
                by_family_json={},
                updated_at=now,
            )
            self._db.add(row)
            self._db.flush()
        row.net_pnl = (row.net_pnl or 0.0) + net_delta
        row.updated_at = now
        if trade_closed:
            row.trades_count = (row.trades_count or 0) + 1
            if win is True:
                row.wins = (row.wins or 0) + 1
            elif win is False:
                row.losses = (row.losses or 0) + 1
        fam = row.by_family_json or {}
        if family and trade_closed and win is not None:
            bucket = fam.get(family) or {"wins": 0, "losses": 0, "pnl": 0.0}
            bucket["pnl"] = bucket.get("pnl", 0.0) + net_delta
            if win:
                bucket["wins"] = bucket.get("wins", 0) + 1
            else:
                bucket["losses"] = bucket.get("losses", 0) + 1
            fam[family] = bucket
            row.by_family_json = fam
        if commit:
            self._db.commit()
            self._db.refresh(row)
        else:
            self._db.flush()
            self._db.refresh(row)
        return row

    def get_daily_summary(self, summary_date: str) -> SpyScalperDailySummary | None:
        return self._db.scalar(
            select(SpyScalperDailySummary).where(SpyScalperDailySummary.summary_date == summary_date)
        )
