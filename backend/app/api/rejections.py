from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.rejection_repository import RejectionRepository
from app.schemas.rejected_trade import RejectedTradeRead

router = APIRouter(tags=["rejections"])


def _iso(dt) -> str:
    return dt.isoformat()


@router.get("/rejections", response_model=list[RejectedTradeRead])
def list_rejections(db: Session = Depends(get_db)) -> list[RejectedTradeRead]:
    repo = RejectionRepository(db)
    return [
        RejectedTradeRead(
            id=r.id,
            candidate_trade_id=r.candidate_trade_id,
            event_analysis_id=r.event_analysis_id,
            reasons=r.reasons,
            rule_codes=r.rule_codes,
            detail=r.detail,
            created_at=_iso(r.created_at),
        )
        for r in repo.list_recent(50)
    ]
