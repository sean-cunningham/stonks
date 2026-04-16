from __future__ import annotations

from typing import Any

from app.models.spy_scalper_daily_summary import SpyScalperDailySummary
from app.models.spy_scalper_position import SpyScalperPosition


def build_daily_metrics(
    summary: SpyScalperDailySummary | None,
    recent_closed: list[SpyScalperPosition],
) -> dict[str, Any]:
    wins = int(summary.wins) if summary else 0
    losses = int(summary.losses) if summary else 0
    total = wins + losses
    win_rate = wins / total if total else 0.0
    gross_win = sum(float(p.realized_pnl or 0) for p in recent_closed if (p.realized_pnl or 0) > 0)
    gross_loss = abs(sum(float(p.realized_pnl or 0) for p in recent_closed if (p.realized_pnl or 0) < 0))
    profit_factor = gross_win / gross_loss if gross_loss > 0 else None
    return {
        "net_pnl": float(summary.net_pnl) if summary else 0.0,
        "trades_count": int(summary.trades_count) if summary else 0,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "by_family": summary.by_family_json if summary else {},
        "recent_expectancy": _expectancy(recent_closed),
    }


def _expectancy(closed: list[SpyScalperPosition]) -> float | None:
    pnls = [float(p.realized_pnl or 0) for p in closed]
    if not pnls:
        return None
    return sum(pnls) / len(pnls)
