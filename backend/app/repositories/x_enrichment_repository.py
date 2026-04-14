from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.x_enrichment import XEnrichment


class XEnrichmentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_recent(self, limit: int = 20) -> list[XEnrichment]:
        q = select(XEnrichment).order_by(desc(XEnrichment.created_at)).limit(limit)
        return list(self._db.scalars(q).all())

    def create(
        self,
        *,
        symbol: str,
        model_name: str,
        sentiment_bias: str,
        acceleration_flag: bool,
        rumor_risk_flag: bool,
        confidence_score: int,
        summary: str,
        evidence_points: list[str],
        provider: str = "xai",
        event_analysis_id: int | None = None,
        candidate_trade_id: int | None = None,
        raw_response_json: str | None = None,
    ) -> XEnrichment:
        row = XEnrichment(
            created_at=utc_now(),
            symbol=symbol.upper(),
            provider=provider,
            model_name=model_name,
            sentiment_bias=sentiment_bias,
            acceleration_flag=acceleration_flag,
            rumor_risk_flag=rumor_risk_flag,
            confidence_score=confidence_score,
            summary=summary,
            evidence_points=evidence_points,
            event_analysis_id=event_analysis_id,
            candidate_trade_id=candidate_trade_id,
            raw_response_json=raw_response_json,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row
