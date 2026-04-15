from typing import Any

from app.core.enums import StrategyType
from app.services.execution.order_dry_run_interface import ValidationResult

ALLOWED = {
    StrategyType.LONG_CALL.value,
    StrategyType.LONG_PUT.value,
    StrategyType.DEBIT_SPREAD.value,
}


def validate_spread_order(order: dict[str, Any]) -> ValidationResult:
    errs: list[str] = []
    strat = order.get("strategy")
    if strat not in ALLOWED:
        errs.append("strategy_not_allowed")
    legs = order.get("legs") or []
    if len(legs) < 1:
        errs.append("no_legs")
    for i, leg in enumerate(legs):
        if not leg.get("symbol"):
            errs.append(f"leg_{i}_missing_symbol")
    option = order.get("option_contract") or {}
    dte = int(option.get("dte", 0))
    delta = abs(float(option.get("delta", 0.0)))
    spread_abs = float(option.get("spread_abs", 999.0))
    mid = max(0.01, float(option.get("mid", 0.01)))
    if dte < 7 or dte > 14:
        errs.append("dte_out_of_range")
    if delta < 0.50 or delta > 0.65:
        errs.append("delta_out_of_range")
    if spread_abs > min(0.08, 0.04 * mid):
        errs.append("contract_spread_too_wide")
    if strat == StrategyType.DEBIT_SPREAD.value:
        spread_mid = max(0.01, float(option.get("spread_mid", mid)))
        spread_ba = float(option.get("spread_bid_ask", spread_abs))
        max_reward = float(option.get("spread_max_reward", 0.0))
        max_risk = float(option.get("spread_max_risk", 0.0))
        if spread_ba > 0.08 * spread_mid:
            errs.append("spread_bidask_too_wide")
        if max_risk <= 0 or (max_reward / max_risk) < 1.2:
            errs.append("spread_reward_risk_too_low")
    return ValidationResult(ok=len(errs) == 0, errors=errs)
