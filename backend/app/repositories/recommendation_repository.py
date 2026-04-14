from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.recommendation_item import RecommendationItem


class RecommendationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_status(self, status: str | None = None, limit: int = 100) -> list[RecommendationItem]:
        q = select(RecommendationItem).order_by(desc(RecommendationItem.created_at)).limit(limit)
        if status:
            q = (
                select(RecommendationItem)
                .where(RecommendationItem.status == status)
                .order_by(desc(RecommendationItem.created_at))
                .limit(limit)
            )
        return list(self._db.scalars(q).all())

    def create(self, row: RecommendationItem) -> RecommendationItem:
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row
