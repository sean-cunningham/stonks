"""Normalized shapes for multi-strategy dashboard API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StrategyStatusBlock(BaseModel):
    strategy_id: str
    display_name: str
    state: str
    pause_reason: str | None = None
    cooldown_until: str | None = None
    paper_only: bool = True
    app_mode: str = "mock"
    open_position_id: int | None = None


class StrategyListItem(BaseModel):
    strategy_id: str
    display_name: str
    description: str
    has_config_put: bool
    has_skipped_feed: bool


class StrategyDashboardBundle(BaseModel):
    """Single payload for shared UI; optional extensions for strategy-specific blocks."""

    status: StrategyStatusBlock
    daily: dict[str, Any] = Field(default_factory=dict)
    balances: dict[str, Any] | None = None
    open_position: dict[str, Any] | None = None
    signals: list[dict[str, Any]] = Field(default_factory=list)
    skipped: list[dict[str, Any]] = Field(default_factory=list)
    trades: list[dict[str, Any]] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    logs: list[dict[str, Any]] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    extensions: dict[str, Any] | None = None
