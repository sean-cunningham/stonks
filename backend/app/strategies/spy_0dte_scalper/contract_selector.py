from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.strategies.spy_0dte_scalper.config import ScalperEffectiveConfig


@dataclass(frozen=True)
class SelectedContract:
    right: str
    strike: float
    expiry: str
    mid: float
    delta: float


def _mock_chain(mid: float, direction: str) -> list[SelectedContract]:
    """Synthetic 0DTE chain around ATM for paper selection."""
    step = 1.0
    atm = round(mid / step) * step
    right = "C" if direction == "call" else "P"
    out: list[SelectedContract] = []
    for i in range(-3, 4):
        k = atm + i * step
        delta = 0.52 + i * 0.025
        delta = max(0.45, min(0.60, delta))
        base_prem = 210.0 - abs(i) * 22.0
        out.append(
            SelectedContract(
                right=right,
                strike=float(k),
                expiry=date.today().isoformat(),
                mid=float(base_prem),
                delta=float(delta),
            )
        )
    return out


def select_contract(
    underlying_mid: float,
    direction: str,
    cfg: ScalperEffectiveConfig,
) -> SelectedContract | None:
    chain = _mock_chain(underlying_mid, direction)
    acceptable: list[SelectedContract] = []
    for leg in chain:
        if not (cfg.delta_min <= leg.delta <= cfg.delta_max):
            continue
        if leg.mid > cfg.premium_hard_max:
            continue
        acceptable.append(leg)
    if not acceptable:
        return None

    def score(leg: SelectedContract) -> float:
        if cfg.premium_target_min <= leg.mid <= cfg.premium_target_max:
            return 0.0
        return abs(leg.mid - (cfg.premium_target_min + cfg.premium_target_max) / 2)

    acceptable.sort(key=score)
    best = acceptable[0]
    spread = max(c.mid for c in acceptable[:3]) - min(c.mid for c in acceptable[:3]) if len(acceptable) >= 2 else 0
    if spread > 80:
        return None
    return best
