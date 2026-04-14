from dataclasses import dataclass


@dataclass
class RiskLimits:
    max_risk_per_trade_pct: float = 3.0
    max_open_positions: int = 1
    max_daily_loss_pct: float = 5.0
    max_weekly_loss_pct: float = 8.0
