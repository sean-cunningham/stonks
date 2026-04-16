from __future__ import annotations

from app.strategies.spy_0dte_scalper.config import ScalperEffectiveConfig


def paper_limit_fill_buy(mid: float, cfg: ScalperEffectiveConfig) -> float:
    """Limit-at-mid with small favorable offset + slippage (long premium = pay up slightly)."""
    slip = cfg.slippage_bps / 10_000.0
    raw = mid + cfg.limit_offset_from_mid
    return max(0.01, raw * (1.0 + slip))


def paper_limit_fill_sell(mid: float, cfg: ScalperEffectiveConfig) -> float:
    slip = cfg.slippage_bps / 10_000.0
    raw = mid - cfg.limit_offset_from_mid
    return max(0.01, raw * (1.0 - slip))
