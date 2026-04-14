from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.trade_repository import TradeRepository
from app.schemas.approved_trade import ApprovedTradeRead

router = APIRouter(tags=["trades"])


def _iso(dt) -> str:
    return dt.isoformat()


@router.get("/trades", response_model=list[ApprovedTradeRead])
def list_trades(db: Session = Depends(get_db)) -> list[ApprovedTradeRead]:
    repo = TradeRepository(db)
    return [
        ApprovedTradeRead(
            id=t.id,
            candidate_trade_id=t.candidate_trade_id,
            event_analysis_id=t.event_analysis_id,
            status=t.status,
            created_at=_iso(t.created_at),
            risk_snapshot=t.risk_snapshot,
            policy_trace=t.policy_trace,
        )
        for t in repo.list_recent_approved(50)
    ]
