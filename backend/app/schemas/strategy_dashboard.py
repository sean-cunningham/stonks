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
    # Event Edge (Strategy 1): whether post-snapshot candidate/approval/paper pipeline runs on live ticks.
    live_candidate_pipeline_enabled: bool | None = None
    # SPY 0DTE scalper (Strategy 2): synthetic scanner disabled outside APP_MODE=mock.
    spy_scalper_synthetic_blocked: bool | None = None
    spy_scalper_synthetic_block_reason: str | None = None


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


class StrategyConfigRead(BaseModel):
    read_only: bool
    effective: dict[str, Any] = Field(default_factory=dict)
    overrides: dict[str, Any] | None = None
    notes: str | None = None


class StrategyDailySummaryRead(BaseModel):
    strategy_id: str
    trade_day: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    details: dict[str, Any] = Field(default_factory=dict)
