from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.candidate_trade import CandidateTrade


class CandidateRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_recent(self, limit: int = 20) -> list[CandidateTrade]:
        q = select(CandidateTrade).order_by(desc(CandidateTrade.created_at)).limit(limit)
        return list(self._db.scalars(q).all())

    def create(
        self,
        *,
        symbol: str,
        strategy: str,
        candidate_kind: str,
        direction_bias: str,
        legs: list,
        market_snapshot_id: int | None = None,
        is_event_driven: bool = False,
        setup_type: str | None = None,
        setup_score: float | None = None,
        reason_codes: list[str] | None = None,
        confirmation_state: str | None = None,
        event_id: str | None = None,
        event_analysis_id: int | None = None,
        metadata: dict | None = None,
        notes: str | None = None,
    ) -> CandidateTrade:
        row = CandidateTrade(
            created_at=utc_now(),
            market_snapshot_id=market_snapshot_id,
            symbol=symbol.upper(),
            strategy=strategy,
            candidate_kind=candidate_kind,
            direction_bias=direction_bias,
            legs=legs,
            is_event_driven=is_event_driven,
            setup_type=setup_type,
            setup_score=setup_score,
            reason_codes=reason_codes,
            confirmation_state=confirmation_state,
            event_id=event_id,
            event_analysis_id=event_analysis_id,
            metadata_json=metadata,
            notes=notes,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def get(self, cid: int) -> CandidateTrade | None:
        return self._db.get(CandidateTrade, cid)
