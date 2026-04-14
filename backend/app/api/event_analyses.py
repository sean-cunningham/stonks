from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.event_analysis_repository import EventAnalysisRepository
from app.schemas.event_analysis import EventAnalysisRead

router = APIRouter(tags=["event-analyses"])


def _iso(dt) -> str:
    return dt.isoformat()


@router.get("/event-analyses", response_model=list[EventAnalysisRead])
def list_event_analyses(db: Session = Depends(get_db)) -> list[EventAnalysisRead]:
    repo = EventAnalysisRepository(db)
    return [
        EventAnalysisRead(
            id=e.id,
            symbol=e.symbol,
            event_type=e.event_type,
            event_source_tier=e.event_source_tier,
            materiality_score=e.materiality_score,
            surprise_score=e.surprise_score,
            direction_bias=e.direction_bias,
            confidence_score=e.confidence_score,
            time_horizon=e.time_horizon,
            priced_in_risk=e.priced_in_risk,
            narrative_summary=e.narrative_summary,
            key_evidence_points=e.key_evidence_points,
            tradeability_flag=e.tradeability_flag,
            recommended_strategy=e.recommended_strategy,
            validation_ok=e.validation_ok,
            escalation_used=e.escalation_used,
            setup_score=e.setup_score,
            reason_codes=e.reason_codes,
            created_at=_iso(e.created_at),
        )
        for e in repo.list_recent(50)
    ]
