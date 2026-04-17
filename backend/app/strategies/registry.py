"""Canonical strategy IDs and metadata for multi-strategy routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


STRATEGY_EVENT_EDGE_V1: Final[str] = "event-edge-v1"
STRATEGY_SPY_0DTE_SCALPER: Final[str] = "spy-0dte-scalper"


@dataclass(frozen=True)
class StrategyMeta:
    strategy_id: str
    display_name: str
    description: str
    db_slug: str | None  # strategy_bot_states slug; None if uses bot_states only
    has_config_put: bool
    has_skipped_feed: bool


def all_strategies() -> list[StrategyMeta]:
    return [
        StrategyMeta(
            strategy_id=STRATEGY_EVENT_EDGE_V1,
            display_name="Event Edge (Strategy A)",
            description="Deterministic intraday ETF options pipeline with approval engine.",
            db_slug=None,
            has_config_put=False,
            has_skipped_feed=True,
        ),
        StrategyMeta(
            strategy_id=STRATEGY_SPY_0DTE_SCALPER,
            display_name="SPY 0DTE Micro-Impulse Scalper",
            description="Isolated SPY 0DTE paper scalper with separate ledger.",
            db_slug=STRATEGY_SPY_0DTE_SCALPER,
            has_config_put=True,
            has_skipped_feed=True,
        ),
    ]


def get_strategy_meta(strategy_id: str) -> StrategyMeta | None:
    for m in all_strategies():
        if m.strategy_id == strategy_id:
            return m
    return None


def is_known_strategy_id(strategy_id: str) -> bool:
    return get_strategy_meta(strategy_id) is not None
