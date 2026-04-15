import logging

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.repositories.event_analysis_repository import EventAnalysisRepository
from app.repositories.x_enrichment_repository import XEnrichmentRepository
from app.services.ai.mock_openai_client import MockOpenAIClient
from app.services.ai.mock_xai_client import MockXaiClient
from app.services.ai.openai_client import OpenAIResponsesClient
from app.services.ai.xai_client import XaiEnrichmentClient
from app.services.events.normalized_packet import NormalizedEventPacket

log = logging.getLogger(__name__)


class EventAnalysisService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._repo = EventAnalysisRepository(db)
        self._x_repo = XEnrichmentRepository(db)

    async def analyze_and_persist(
        self,
        packet: NormalizedEventPacket,
    ) -> tuple[object | None, str | None]:
        use_mock = self._settings.use_mock_openai or not self._settings.openai_enable_real_calls
        escalation = packet.event_kind in ("macro_announcement", "sec_filing")
        try:
            if use_mock:
                client: MockOpenAIClient | OpenAIResponsesClient = MockOpenAIClient()
                raw, judgment = await client.analyze_event(packet, escalation=escalation)
            else:
                client = OpenAIResponsesClient(self._settings)
                raw, judgment = await client.analyze_event(packet, escalation=escalation)
        except (ValidationError, ValueError) as e:
            log.warning("event analysis failed: %s", e)
            return None, str(e)
        except Exception as e:
            log.exception("openai call failed")
            return None, str(e)

        row = self._repo.create_from_judgment(
            judgment,
            raw_json=raw,
            validation_ok=True,
            normalized_event_id=packet.dedupe_key,
            event_source_tier=_source_tier(packet.source),
            escalation_used=escalation,
            setup_score=float(judgment.materiality_score),
            reason_codes=[packet.event_kind, "openai_primary"],
        )
        await self._maybe_enrich_with_xai(packet, row.id, judgment.materiality_score)
        return row, None

    async def _maybe_enrich_with_xai(self, packet: NormalizedEventPacket, event_analysis_id: int, materiality_score: int) -> None:
        if self._settings.v1_disable_xai_runtime:
            return
        if not self._settings.xai_enable_x_search_enrichment:
            return
        if materiality_score < self._settings.xai_enrichment_min_materiality_score:
            return
        allow_symbols = {s.strip().upper() for s in self._settings.xai_enrichment_symbol_allowlist.split(",") if s.strip()}
        allow_types = {s.strip() for s in self._settings.xai_enrichment_event_types.split(",") if s.strip()}
        if packet.symbol.upper() not in allow_symbols or packet.event_kind not in allow_types:
            return
        if len(self._x_repo.list_recent(self._settings.xai_enrichment_max_calls_per_day)) >= self._settings.xai_enrichment_max_calls_per_day:
            return
        try:
            if self._settings.use_mock_xai or not self._settings.xai_enable_real_calls:
                raw, payload = await MockXaiClient().enrich_event(packet)
            else:
                raw, payload = await XaiEnrichmentClient(self._settings).enrich_event(packet)
            self._x_repo.create(
                symbol=packet.symbol,
                event_analysis_id=event_analysis_id,
                model_name=self._settings.xai_enrichment_model,
                sentiment_bias=str(payload.get("sentiment_bias", "mixed")),
                acceleration_flag=bool(payload.get("acceleration_flag", False)),
                rumor_risk_flag=bool(payload.get("rumor_risk_flag", False)),
                confidence_score=int(payload.get("confidence_score", 0)),
                summary=str(payload.get("summary", "")),
                evidence_points=list(payload.get("evidence_points", [])),
                raw_response_json=raw,
            )
        except Exception:
            log.exception("xai enrichment sidecar failed")


def _source_tier(source: str) -> str:
    s = source.lower()
    if s.startswith("mock") or "news" in s:
        return "supplemental"
    return "official"
