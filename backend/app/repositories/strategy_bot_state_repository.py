from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.strategy_bot_state import StrategyBotState

SPY_SCALPER_SLUG = "spy-0dte-scalper"


class StrategyBotStateRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_or_create(self, strategy_slug: str) -> StrategyBotState:
        row = self._db.scalar(select(StrategyBotState).where(StrategyBotState.strategy_slug == strategy_slug))
        if row:
            return row
        now = utc_now()
        row = StrategyBotState(
            strategy_slug=strategy_slug,
            state="stopped",
            pause_reason=None,
            cooldown_until=None,
            config_json=None,
            scalper_state_json=None,
            updated_at=now,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def set_state(
        self,
        strategy_slug: str,
        state: str,
        *,
        pause_reason: str | None = None,
        cooldown_until=None,
    ) -> StrategyBotState:
        row = self.get_or_create(strategy_slug)
        row.state = state
        row.pause_reason = pause_reason
        row.cooldown_until = cooldown_until
        row.updated_at = utc_now()
        self._db.commit()
        self._db.refresh(row)
        return row

    def update_scalper_state_json(
        self, strategy_slug: str, data: dict | None, *, commit: bool = True
    ) -> StrategyBotState:
        row = self.get_or_create(strategy_slug)
        row.scalper_state_json = data
        row.updated_at = utc_now()
        if commit:
            self._db.commit()
            self._db.refresh(row)
        else:
            self._db.flush()
            self._db.refresh(row)
        return row

    def update_config_json(self, strategy_slug: str, data: dict | None) -> StrategyBotState:
        row = self.get_or_create(strategy_slug)
        row.config_json = data
        row.updated_at = utc_now()
        self._db.commit()
        self._db.refresh(row)
        return row

    def set_cooldown(self, strategy_slug: str, until, *, commit: bool = True) -> StrategyBotState:
        row = self.get_or_create(strategy_slug)
        row.cooldown_until = until
        row.updated_at = utc_now()
        if commit:
            self._db.commit()
            self._db.refresh(row)
        else:
            self._db.flush()
            self._db.refresh(row)
        return row
