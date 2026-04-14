from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.trade_review import TradeReview


class TradeReviewRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_approved_trade_id(self, approved_trade_id: int) -> TradeReview | None:
        q = select(TradeReview).where(TradeReview.approved_trade_id == approved_trade_id)
        return self._db.scalars(q).first()

    def get_by_id(self, review_id: int) -> TradeReview | None:
        return self._db.get(TradeReview, review_id)

    def list_recent(self, limit: int = 200) -> list[TradeReview]:
        q = select(TradeReview).order_by(TradeReview.created_at.desc()).limit(limit)
        return list(self._db.scalars(q).all())

    def create(self, row: TradeReview) -> TradeReview:
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row
