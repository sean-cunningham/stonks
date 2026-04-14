from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.parameter_experiment_result import ParameterExperimentResult


class ParameterExperimentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_review(self, trade_review_id: int) -> list[ParameterExperimentResult]:
        q = select(ParameterExperimentResult).where(ParameterExperimentResult.trade_review_id == trade_review_id)
        return list(self._db.scalars(q).all())

    def create(self, row: ParameterExperimentResult) -> ParameterExperimentResult:
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row
