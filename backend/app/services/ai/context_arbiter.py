from __future__ import annotations

from dataclasses import dataclass

from app.models.event_analysis import EventAnalysis


@dataclass
class PrimaryContextOutput:
    context_state: str
    affected_symbols: list[str]
    reason_codes: list[str]
    confidence_penalty: int
    expires_in_minutes: int


@dataclass
class AdversarialContextOutput:
    alternative_interpretation: str
    threat_level: str
    trade_action: str
    reason_codes: list[str]
    expires_in_minutes: int


@dataclass
class ArbiterDecision:
    action: str
    require_confirmation: bool
    size_tier_delta: int
    blocked: bool
    reason_codes: list[str]


def primary_context_agent(event_row: EventAnalysis | None, symbol: str) -> PrimaryContextOutput:
    if not event_row:
        return PrimaryContextOutput("ignore", [symbol], [], 0, 0)
    mat = int(event_row.materiality_score or 0)
    mixed = (event_row.direction_bias or "").lower() == "mixed"
    if mixed and mat >= 60:
        return PrimaryContextOutput("block", [symbol], ["mixed_high_materiality"], 40, 30)
    if mat >= 80:
        return PrimaryContextOutput("caution", [symbol], ["high_materiality"], 20, 20)
    if mat >= 60:
        return PrimaryContextOutput("watch", [symbol], ["moderate_materiality"], 10, 15)
    return PrimaryContextOutput("ignore", [symbol], ["low_materiality"], 0, 0)


def adversarial_context_agent(event_row: EventAnalysis | None) -> AdversarialContextOutput:
    if not event_row:
        return AdversarialContextOutput("no event narrative", "low", "none", [], 0)
    txt = (event_row.narrative_summary or "").lower()
    if "uncertain" in txt or "rumor" in txt:
        return AdversarialContextOutput(
            "headline may be over-interpreted by trend followers",
            "medium",
            "require_confirmation",
            ["adversarial_uncertainty"],
            20,
        )
    if event_row.direction_bias == "mixed":
        return AdversarialContextOutput(
            "signals conflict; downside tail not priced",
            "high",
            "block",
            ["adversarial_conflict"],
            30,
        )
    return AdversarialContextOutput("no strong alternative risk", "low", "none", [], 0)


def deterministic_context_arbiter(
    *,
    primary: PrimaryContextOutput,
    adversarial: AdversarialContextOutput,
) -> ArbiterDecision:
    reason_codes = list(primary.reason_codes) + list(adversarial.reason_codes)
    if primary.context_state == "block" or adversarial.trade_action == "block":
        return ArbiterDecision("block", False, 0, True, reason_codes)
    if adversarial.trade_action == "require_confirmation":
        return ArbiterDecision("require_confirmation", True, 0, False, reason_codes)
    if primary.context_state == "caution":
        return ArbiterDecision("reduce_size", False, -1, False, reason_codes)
    return ArbiterDecision("none", False, 0, False, reason_codes)
