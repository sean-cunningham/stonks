def max_risk_dollars(equity: float, max_risk_pct: float) -> float:
    return max(0.0, equity * (max_risk_pct / 100.0))


def per_contract_budget(max_risk: float, contracts: int = 1) -> float:
    if contracts <= 0:
        return 0.0
    return max_risk / contracts
