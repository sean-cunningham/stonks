from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.decision_snapshot_repository import DecisionSnapshotRepository
from app.schemas.decision_snapshot import DecisionSnapshotRead

router = APIRouter(tags=["decisions"])


def _iso(dt) -> str:
    return dt.isoformat() if dt else ""


@router.get("/decisions", response_model=list[DecisionSnapshotRead])
def list_decisions(db: Session = Depends(get_db)) -> list[DecisionSnapshotRead]:
    rows = DecisionSnapshotRepository(db).list_recent(200)
    return [
        DecisionSnapshotRead(
            id=r.id,
            created_at=_iso(r.created_at),
            symbol=r.symbol,
            candidate_trade_id=r.candidate_trade_id,
            approved_trade_id=r.approved_trade_id,
            bucket=r.bucket,
            strategy_track=r.strategy_track,
            hard_vetoes=r.hard_vetoes,
            hard_veto_codes=r.hard_veto_codes,
            scores=r.scores,
            weighted_score=r.weighted_score,
            explanation=r.explanation,
        )
        for r in rows
    ]
