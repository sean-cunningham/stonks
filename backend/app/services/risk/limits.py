from dataclasses import dataclass


@dataclass
class RiskLimits:
    max_risk_per_trade_pct: float = 1.0
    max_open_positions: int = 2
    max_open_positions_per_symbol: int = 1
    max_combined_open_risk_pct: float = 3.0
    max_daily_loss_pct: float = 5.0
    max_weekly_loss_pct: float = 8.0
