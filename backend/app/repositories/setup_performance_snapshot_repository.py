from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.setup_performance_snapshot import SetupPerformanceSnapshot


class SetupPerformanceSnapshotRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def latest_for_dimension(self, dimension_type: str, dimension_key: str) -> SetupPerformanceSnapshot | None:
        q = (
            select(SetupPerformanceSnapshot)
            .where(
                SetupPerformanceSnapshot.dimension_type == dimension_type,
                SetupPerformanceSnapshot.dimension_key == dimension_key,
            )
            .order_by(desc(SetupPerformanceSnapshot.computed_at))
            .limit(1)
        )
        return self._db.scalars(q).first()

    def save_snapshot(self, row: SetupPerformanceSnapshot) -> SetupPerformanceSnapshot:
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row
