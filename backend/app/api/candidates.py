from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.candidate_trade import CandidateTradeRead

router = APIRouter(tags=["candidates"])


def _iso(dt) -> str:
    return dt.isoformat()


@router.get("/candidates", response_model=list[CandidateTradeRead])
def list_candidates(db: Session = Depends(get_db)) -> list[CandidateTradeRead]:
    repo = CandidateRepository(db)
    return [
        CandidateTradeRead(
            id=c.id,
            symbol=c.symbol,
            strategy=c.strategy,
            candidate_kind=c.candidate_kind,
            direction_bias=c.direction_bias,
            legs=c.legs,
            is_event_driven=c.is_event_driven,
            setup_type=c.setup_type,
            setup_score=c.setup_score,
            reason_codes=c.reason_codes,
            confirmation_state=c.confirmation_state,
            event_id=c.event_id,
            event_analysis_id=c.event_analysis_id,
            created_at=_iso(c.created_at),
            notes=c.notes,
        )
        for c in repo.list_recent(50)
    ]
