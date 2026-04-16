from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScalperRuntimeState:
    trade_day: str
    consecutive_losses: int = 0
    disabled_families: list[str] = field(default_factory=list)
    ai_calls_today: int = 0
    deployable_cash: float = 4000.0
    last_exit_was_fast_loser: bool = False

    @staticmethod
    def from_json(raw: dict[str, Any] | None, trade_day: str, default_deployable: float) -> ScalperRuntimeState:
        if not raw or raw.get("trade_day") != trade_day:
            return ScalperRuntimeState(
                trade_day=trade_day,
                consecutive_losses=0,
                disabled_families=[],
                ai_calls_today=0,
                deployable_cash=default_deployable,
                last_exit_was_fast_loser=False,
            )
        return ScalperRuntimeState(
            trade_day=trade_day,
            consecutive_losses=int(raw.get("consecutive_losses", 0)),
            disabled_families=list(raw.get("disabled_families") or []),
            ai_calls_today=int(raw.get("ai_calls_today", 0)),
            deployable_cash=float(raw.get("deployable_cash", default_deployable)),
            last_exit_was_fast_loser=bool(raw.get("last_exit_was_fast_loser", False)),
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "trade_day": self.trade_day,
            "consecutive_losses": self.consecutive_losses,
            "disabled_families": self.disabled_families,
            "ai_calls_today": self.ai_calls_today,
            "deployable_cash": self.deployable_cash,
            "last_exit_was_fast_loser": self.last_exit_was_fast_loser,
        }
