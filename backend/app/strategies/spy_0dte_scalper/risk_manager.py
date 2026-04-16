from __future__ import annotations

from dataclasses import dataclass

from app.strategies.spy_0dte_scalper.config import ScalperEffectiveConfig
from app.strategies.spy_0dte_scalper.state import ScalperRuntimeState


@dataclass(frozen=True)
class RiskDecision:
    ok: bool
    reason: str | None = None


def evaluate_new_entry(
    cfg: ScalperEffectiveConfig,
    runtime: ScalperRuntimeState,
    *,
    trades_today: int,
    daily_net_pnl: float,
    setup_family: str,
    has_open_position: bool,
) -> RiskDecision:
    if has_open_position:
        return RiskDecision(False, "open_position")
    if trades_today >= cfg.max_trades_per_day:
        return RiskDecision(False, "max_trades_day")
    if runtime.consecutive_losses >= cfg.max_consecutive_losses:
        return RiskDecision(False, "max_consecutive_losses")
    if daily_net_pnl <= -cfg.daily_hard_stop_loss:
        return RiskDecision(False, "daily_hard_stop")
    if daily_net_pnl <= -cfg.daily_soft_stop_loss:
        return RiskDecision(False, "daily_soft_stop")
    if setup_family in runtime.disabled_families:
        return RiskDecision(False, "family_disabled")
    if runtime.deployable_cash < cfg.reserve_cash + cfg.premium_hard_max:
        return RiskDecision(False, "deployable_cash_low")
    return RiskDecision(True, None)
