from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.event_analysis import EventAnalysis
from app.schemas.event_analysis import EventAnalysisJudgment


class EventAnalysisRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_recent(self, limit: int = 20) -> list[EventAnalysis]:
        q = select(EventAnalysis).order_by(desc(EventAnalysis.created_at)).limit(limit)
        return list(self._db.scalars(q).all())

    def create_from_judgment(
        self,
        j: EventAnalysisJudgment,
        *,
        raw_json: str | None,
        validation_ok: bool,
        normalized_event_id: str | None = None,
        event_source_tier: str = "official",
        escalation_used: bool = False,
        setup_score: float | None = None,
        reason_codes: list[str] | None = None,
    ) -> EventAnalysis:
        row = EventAnalysis(
            created_at=utc_now(),
            symbol=j.symbol.upper(),
            normalized_event_id=normalized_event_id,
            event_source_tier=event_source_tier,
            event_type=j.event_type.value,
            materiality_score=j.materiality_score,
            surprise_score=j.surprise_score,
            direction_bias=j.direction_bias.value,
            confidence_score=j.confidence_score,
            time_horizon=j.time_horizon.value,
            priced_in_risk=j.priced_in_risk.value,
            narrative_summary=j.narrative_summary,
            key_evidence_points=j.key_evidence_points,
            tradeability_flag=j.tradeability_flag,
            recommended_strategy=j.recommended_strategy.value,
            raw_response_json=raw_json,
            validation_ok=validation_ok,
            escalation_used=escalation_used,
            setup_score=setup_score,
            reason_codes=reason_codes,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row
