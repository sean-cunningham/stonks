from datetime import UTC, datetime

from app.services.events.normalized_packet import NormalizedEventPacket


class MockEventProvider:
    """Sample packets for mock mode / tests."""

    def poll(self) -> list[NormalizedEventPacket]:
        now = datetime.now(UTC)
        return [
            NormalizedEventPacket(
                source="mock_earnings",
                event_kind="earnings",
                symbol="NVDA",
                headline="NVDA Q1 EPS beats consensus",
                body="Revenue +22% YoY; data center strong.",
                occurred_at=now,
                metadata={"fiscal_q": "Q1"},
                dedupe_key="mock-earnings-nvda-1",
            ),
            NormalizedEventPacket(
                source="mock_sec",
                event_kind="sec_filing",
                symbol="AAPL",
                headline="Form 8-K: leadership change",
                body=None,
                occurred_at=now,
                metadata={"form": "8-K"},
                dedupe_key="mock-sec-aapl-1",
            ),
            NormalizedEventPacket(
                source="mock_macro",
                event_kind="macro_announcement",
                symbol="SPY",
                headline="Fed holds rates steady",
                body="Statement skewed balanced.",
                occurred_at=now,
                metadata={},
                dedupe_key="mock-macro-spy-1",
            ),
        ]
