from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.bot_state import BotStateRow


class BotStateRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self) -> BotStateRow:
        row = self._db.scalar(select(BotStateRow).where(BotStateRow.id == 1))
        if row:
            return row
        row = BotStateRow(
            id=1,
            state="stopped",
            pause_reason=None,
            cooldown_until=None,
            updated_at=utc_now(),
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def set_state(
        self,
        state: str,
        *,
        pause_reason: str | None = None,
        cooldown_until=None,
    ) -> BotStateRow:
        row = self.get()
        row.state = state
        row.pause_reason = pause_reason
        row.cooldown_until = cooldown_until
        row.updated_at = utc_now()
        self._db.commit()
        self._db.refresh(row)
        return row
