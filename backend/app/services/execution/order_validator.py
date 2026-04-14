from typing import Any

from app.core.enums import StrategyType
from app.services.execution.order_dry_run_interface import ValidationResult

ALLOWED = {s.value for s in StrategyType}


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
    return ValidationResult(ok=len(errs) == 0, errors=errs)
