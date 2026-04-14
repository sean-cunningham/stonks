from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]


class OrderDryRunnable(Protocol):
    def dry_run(self, order: dict[str, Any]) -> ValidationResult:
        ...
