from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.rejected_trade import RejectedTrade


class RejectionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_recent(self, limit: int = 20) -> list[RejectedTrade]:
        q = select(RejectedTrade).order_by(desc(RejectedTrade.created_at)).limit(limit)
        return list(self._db.scalars(q).all())

    def create(
        self,
        *,
        reasons: list,
        rule_codes: list | None = None,
        candidate_trade_id: int | None = None,
        event_analysis_id: int | None = None,
        detail: str | None = None,
    ) -> RejectedTrade:
        row = RejectedTrade(
            created_at=utc_now(),
            candidate_trade_id=candidate_trade_id,
            event_analysis_id=event_analysis_id,
            reasons=reasons,
            rule_codes=rule_codes or [],
            detail=detail,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row
