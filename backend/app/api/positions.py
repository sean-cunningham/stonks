from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.position_repository import PositionRepository
from app.schemas.active_position import ActivePositionRead

router = APIRouter(tags=["positions"])


def _iso(dt) -> str:
    return dt.isoformat()


@router.get("/positions", response_model=list[ActivePositionRead])
def list_positions(
    include_closed: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[ActivePositionRead]:
    repo = PositionRepository(db)
    rows = repo.list_recent(50, include_closed=include_closed)
    return [
        ActivePositionRead(
            id=p.id,
            symbol=p.symbol,
            strategy=p.strategy,
            status=p.status,
            quantity=p.quantity,
            average_entry_price=p.average_entry_price,
            market_value=p.market_value,
            unrealized_pnl=p.unrealized_pnl,
            initial_stop_price=p.initial_stop_price,
            emergency_premium_stop_pct=p.emergency_premium_stop_pct,
            current_trailing_stop=p.current_trailing_stop,
            breakeven_armed=p.breakeven_armed,
            partial_exit_taken=p.partial_exit_taken,
            partial_exit_qty=p.partial_exit_qty,
            thesis_expires_at=_iso(p.thesis_expires_at) if p.thesis_expires_at else None,
            high_water_mark_price=p.high_water_mark_price,
            low_water_mark_price=p.low_water_mark_price,
            reached_1r=p.reached_1r,
            reached_1_5r=p.reached_1_5r,
            reached_2r=p.reached_2r,
            opened_at=_iso(p.opened_at),
            closed_at=_iso(p.closed_at) if p.closed_at else None,
            legs=p.legs,
        )
        for p in rows
    ]
