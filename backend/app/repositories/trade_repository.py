from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.approved_trade import ApprovedTrade
from app.models.fill import Fill


class TradeRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_recent_approved(self, limit: int = 20) -> list[ApprovedTrade]:
        q = select(ApprovedTrade).order_by(desc(ApprovedTrade.created_at)).limit(limit)
        return list(self._db.scalars(q).all())

    def list_recent_fills(self, limit: int = 30) -> list[Fill]:
        q = select(Fill).order_by(desc(Fill.created_at)).limit(limit)
        return list(self._db.scalars(q).all())

    def create_approved(
        self,
        *,
        candidate_trade_id: int,
        event_analysis_id: int | None,
        status: str = "pending",
        risk_snapshot: dict | None = None,
        policy_trace: dict | None = None,
    ) -> ApprovedTrade:
        row = ApprovedTrade(
            created_at=utc_now(),
            candidate_trade_id=candidate_trade_id,
            event_analysis_id=event_analysis_id,
            status=status,
            risk_snapshot=risk_snapshot,
            policy_trace=policy_trace,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row
