from dataclasses import dataclass


@dataclass
class SetupInputs:
    materiality_score: int
    confidence_score: int
    liquidity_ok: bool
    confirmation_ok: bool
    cross_market_ok: bool
    rumor_risk_flag: bool
    event_mixed: bool


def score_setup(i: SetupInputs) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    score += min(30.0, i.materiality_score * 0.3)
    score += min(25.0, i.confidence_score * 0.25)
    if i.liquidity_ok:
        score += 15.0
        reasons.append("liquidity_ok")
    else:
        reasons.append("liquidity_poor")
    if i.confirmation_ok:
        score += 20.0
        reasons.append("price_confirmation_ok")
    else:
        reasons.append("price_confirmation_weak")
    if i.cross_market_ok:
        score += 10.0
        reasons.append("cross_market_ok")
    else:
        reasons.append("cross_market_missing")
    if i.event_mixed:
        score -= 20.0
        reasons.append("event_mixed")
    if i.rumor_risk_flag:
        score -= 25.0
        reasons.append("rumor_risk_high")
    return max(0.0, min(100.0, score)), reasons
