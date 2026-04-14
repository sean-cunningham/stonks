from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.active_position import ActivePosition


class PositionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_open(self) -> list[ActivePosition]:
        q = select(ActivePosition).where(ActivePosition.status == "open")
        return list(self._db.scalars(q).all())

    def list_recent(self, limit: int = 20, *, include_closed: bool = True) -> list[ActivePosition]:
        q = select(ActivePosition).order_by(desc(ActivePosition.opened_at)).limit(limit)
        if not include_closed:
            q = (
                select(ActivePosition)
                .where(ActivePosition.status == "open")
                .order_by(desc(ActivePosition.opened_at))
                .limit(limit)
            )
        return list(self._db.scalars(q).all())

    def create_open(
        self,
        *,
        approved_trade_id: int,
        symbol: str,
        strategy: str,
        legs: list,
        quantity: int,
        average_entry_price: float,
        market_value: float | None = None,
        unrealized_pnl: float | None = None,
        initial_stop_price: float | None = None,
        emergency_premium_stop_pct: float | None = None,
        thesis_expires_at=None,
    ) -> ActivePosition:
        row = ActivePosition(
            approved_trade_id=approved_trade_id,
            symbol=symbol.upper(),
            strategy=strategy,
            status="open",
            legs=legs,
            quantity=quantity,
            average_entry_price=average_entry_price,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl,
            initial_stop_price=initial_stop_price,
            emergency_premium_stop_pct=emergency_premium_stop_pct,
            current_trailing_stop=initial_stop_price,
            breakeven_armed=False,
            partial_exit_taken=False,
            partial_exit_qty=0,
            thesis_expires_at=thesis_expires_at,
            high_water_mark_price=average_entry_price,
            low_water_mark_price=average_entry_price,
            reached_1r=False,
            reached_1_5r=False,
            reached_2r=False,
            opened_at=utc_now(),
            closed_at=None,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row
