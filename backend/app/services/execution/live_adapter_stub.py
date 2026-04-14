"""Placeholder for future live broker — dry-run only."""

from typing import Any

from app.services.execution.order_dry_run_interface import ValidationResult
from app.services.execution.order_validator import validate_spread_order


class FutureLiveBrokerExecutionAdapter:
    def dry_run(self, order: dict[str, Any]) -> ValidationResult:
        return validate_spread_order(order)

    def place_live(self, _order: dict[str, Any]) -> None:
        raise NotImplementedError("Live trading not enabled in v1")
