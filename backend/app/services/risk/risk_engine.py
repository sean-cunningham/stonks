from dataclasses import dataclass

from app.core.clock import utc_now
from app.models.account import Account
from app.models.bot_state import BotStateRow
from app.services.risk.limits import RiskLimits
from app.services.risk.sizing import max_risk_dollars


@dataclass
class RiskCheckResult:
    ok: bool
    reasons: list[str]


def check_risk(
    *,
    account: Account,
    bot: BotStateRow,
    open_position_count: int,
    limits: RiskLimits | None = None,
) -> RiskCheckResult:
    lim = limits or RiskLimits()
    reasons: list[str] = []
    if bot.state != "running":
        reasons.append("bot_not_running")
    if bot.cooldown_until and utc_now() < bot.cooldown_until:
        reasons.append("cooldown_active")
    if open_position_count >= lim.max_open_positions:
        reasons.append("max_positions")
    daily_loss_pct = 0.0
    weekly_loss_pct = 0.0
    if account.equity > 0:
        daily_loss_pct = max(0.0, -account.realized_pnl) / account.equity * 100
        weekly_loss_pct = daily_loss_pct
    if account.realized_pnl < 0 and daily_loss_pct >= lim.max_daily_loss_pct:
        reasons.append("daily_loss_breach")
    if account.realized_pnl < 0 and weekly_loss_pct >= lim.max_weekly_loss_pct:
        reasons.append("weekly_loss_breach")
    max_risk = max_risk_dollars(account.equity, lim.max_risk_per_trade_pct)
    if max_risk <= 0:
        reasons.append("zero_risk_budget")
    return RiskCheckResult(ok=len(reasons) == 0, reasons=reasons)
