from app.schemas.event_analysis import EventAnalysisJudgment
from app.services.events.normalized_packet import NormalizedEventPacket


class MockOpenAIClient:
    async def analyze_event(
        self,
        packet: NormalizedEventPacket,
        *,
        escalation: bool = False,
    ) -> tuple[str, EventAnalysisJudgment]:
        materiality = 80 if packet.event_kind in ("earnings", "sec_filing", "macro_announcement") else 45
        confidence = 70 if escalation else 55
        direction = "bullish" if "beat" in packet.headline.lower() else "mixed"
        j = EventAnalysisJudgment(
            event_type=packet.event_kind if packet.event_kind in {
                "earnings", "sec_filing", "macro_announcement", "headline", "guidance_change", "transcript"
            } else "other",
            symbol=packet.symbol.upper(),
            materiality_score=materiality,
            surprise_score=55,
            direction_bias=direction,
            confidence_score=confidence,
            time_horizon="intraday",
            priced_in_risk="medium",
            narrative_summary="Primary catalyst appears relevant for short-term options positioning. Follow-through confirmation is required.",
            key_evidence_points=[packet.headline[:120]],
            tradeability_flag=materiality >= 50 and direction != "none",
            recommended_strategy="debit_spread" if direction == "bullish" else "none",
        )
        return j.model_dump_json(), j
