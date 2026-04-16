from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import Settings


@dataclass(frozen=True)
class ScalperEffectiveConfig:
    paper_only: bool
    reserve_cash: float
    deployable_target: float
    max_trades_per_day: int
    max_consecutive_losses: int
    pre_ai_min_score: float
    ai_max_calls_per_day: int
    delta_min: float
    delta_max: float
    premium_target_min: float
    premium_target_max: float
    premium_hard_max: float
    max_hold_minutes: float
    fast_fail_minutes: float
    cooldown_after_exit_seconds: int
    cooldown_after_fast_loser_seconds: int
    daily_hard_stop_loss: float
    daily_soft_stop_loss: float
    limit_offset_from_mid: float
    cancel_window_seconds: int
    slippage_bps: float
    tp_pct: float = 0.08
    stop_pct: float = 0.12


def merge_overrides(base: dict[str, Any], overrides: dict[str, Any] | None) -> dict[str, Any]:
    if not overrides:
        return dict(base)
    out = dict(base)
    for k, v in overrides.items():
        if v is not None:
            out[k] = v
    return out


def effective_config(settings: Settings, config_json: dict[str, Any] | None) -> ScalperEffectiveConfig:
    base = {
        "paper_only": settings.spy_scalper_paper_only,
        "reserve_cash": settings.spy_scalper_reserve_cash,
        "deployable_target": settings.spy_scalper_deployable_target,
        "max_trades_per_day": settings.spy_scalper_max_trades_per_day,
        "max_consecutive_losses": settings.spy_scalper_max_consecutive_losses,
        "pre_ai_min_score": settings.spy_scalper_pre_ai_min_score,
        "ai_max_calls_per_day": settings.spy_scalper_ai_max_calls_per_day,
        "delta_min": settings.spy_scalper_contract_delta_min,
        "delta_max": settings.spy_scalper_contract_delta_max,
        "premium_target_min": settings.spy_scalper_premium_target_min,
        "premium_target_max": settings.spy_scalper_premium_target_max,
        "premium_hard_max": settings.spy_scalper_premium_hard_max,
        "max_hold_minutes": settings.spy_scalper_max_hold_minutes,
        "fast_fail_minutes": settings.spy_scalper_fast_fail_minutes,
        "cooldown_after_exit_seconds": settings.spy_scalper_cooldown_after_exit_seconds,
        "cooldown_after_fast_loser_seconds": settings.spy_scalper_cooldown_after_fast_loser_seconds,
        "daily_hard_stop_loss": settings.spy_scalper_daily_hard_stop_loss,
        "daily_soft_stop_loss": settings.spy_scalper_daily_soft_stop_loss,
        "limit_offset_from_mid": settings.spy_scalper_limit_offset_from_mid,
        "cancel_window_seconds": settings.spy_scalper_cancel_window_seconds,
        "slippage_bps": settings.spy_scalper_slippage_bps,
        "tp_pct": 0.08,
        "stop_pct": 0.12,
    }
    merged = merge_overrides(base, config_json)
    paper_only = bool(merged["paper_only"])
    if settings.spy_scalper_paper_only:
        paper_only = True
    return ScalperEffectiveConfig(
        paper_only=paper_only,
        reserve_cash=float(merged["reserve_cash"]),
        deployable_target=float(merged["deployable_target"]),
        max_trades_per_day=int(merged["max_trades_per_day"]),
        max_consecutive_losses=int(merged["max_consecutive_losses"]),
        pre_ai_min_score=float(merged["pre_ai_min_score"]),
        ai_max_calls_per_day=int(merged["ai_max_calls_per_day"]),
        delta_min=float(merged["delta_min"]),
        delta_max=float(merged["delta_max"]),
        premium_target_min=float(merged["premium_target_min"]),
        premium_target_max=float(merged["premium_target_max"]),
        premium_hard_max=float(merged["premium_hard_max"]),
        max_hold_minutes=float(merged["max_hold_minutes"]),
        fast_fail_minutes=float(merged["fast_fail_minutes"]),
        cooldown_after_exit_seconds=int(merged["cooldown_after_exit_seconds"]),
        cooldown_after_fast_loser_seconds=int(merged["cooldown_after_fast_loser_seconds"]),
        daily_hard_stop_loss=float(merged["daily_hard_stop_loss"]),
        daily_soft_stop_loss=float(merged["daily_soft_stop_loss"]),
        limit_offset_from_mid=float(merged["limit_offset_from_mid"]),
        cancel_window_seconds=int(merged["cancel_window_seconds"]),
        slippage_bps=float(merged["slippage_bps"]),
        tp_pct=float(merged.get("tp_pct", 0.08)),
        stop_pct=float(merged.get("stop_pct", 0.12)),
    )
