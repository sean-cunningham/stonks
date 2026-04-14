from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.x_enrichment_repository import XEnrichmentRepository
from app.schemas.x_enrichment import XEnrichmentRead

router = APIRouter(tags=["x-enrichments"])


def _iso(dt) -> str:
    return dt.isoformat()


@router.get("/x-enrichments", response_model=list[XEnrichmentRead])
def list_x_enrichments(db: Session = Depends(get_db)) -> list[XEnrichmentRead]:
    repo = XEnrichmentRepository(db)
    return [
        XEnrichmentRead(
            id=x.id,
            symbol=x.symbol,
            provider=x.provider,
            model_name=x.model_name,
            sentiment_bias=x.sentiment_bias,
            acceleration_flag=x.acceleration_flag,
            rumor_risk_flag=x.rumor_risk_flag,
            confidence_score=x.confidence_score,
            summary=x.summary,
            evidence_points=x.evidence_points,
            event_analysis_id=x.event_analysis_id,
            candidate_trade_id=x.candidate_trade_id,
            created_at=_iso(x.created_at),
        )
        for x in repo.list_recent(100)
    ]
