from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.decision_snapshot import DecisionSnapshot


class DecisionSnapshotRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        symbol: str,
        candidate_trade_id: int | None,
        event_analysis_id: int | None,
        approved_trade_id: int | None,
        bucket: str,
        strategy_track: str,
        hard_vetoes: list[str],
        hard_veto_codes: list[str],
        scores: dict | None,
        weighted_score: float | None,
        market_state_json: dict,
        option_state_json: dict,
        risk_state_json: dict,
        context_state_json: dict,
        historical_state_json: dict,
        order_instruction_json: dict | None,
        explanation: str | None,
    ) -> DecisionSnapshot:
        row = DecisionSnapshot(
            created_at=utc_now(),
            symbol=symbol.upper(),
            candidate_trade_id=candidate_trade_id,
            event_analysis_id=event_analysis_id,
            approved_trade_id=approved_trade_id,
            bucket=bucket,
            strategy_track=strategy_track,
            hard_vetoes=hard_vetoes,
            hard_veto_codes=hard_veto_codes,
            scores=scores,
            weighted_score=weighted_score,
            market_state_json=market_state_json,
            option_state_json=option_state_json,
            risk_state_json=risk_state_json,
            context_state_json=context_state_json,
            historical_state_json=historical_state_json,
            order_instruction_json=order_instruction_json,
            explanation=explanation,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def list_recent(self, limit: int = 200) -> list[DecisionSnapshot]:
        q = select(DecisionSnapshot).order_by(desc(DecisionSnapshot.created_at)).limit(limit)
        return list(self._db.scalars(q).all())
