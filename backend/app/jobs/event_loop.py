import logging

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.repositories.bot_state_repository import BotStateRepository
from app.services.ai.event_analysis_service import EventAnalysisService
from app.services.events.mock_event_provider import MockEventProvider
from app.services.events.thenewsapi_provider import TheNewsApiProvider

log = logging.getLogger(__name__)


def run_event_tick(db: Session, settings: Settings) -> None:
    bot = BotStateRepository(db).get()
    if bot.state != "running":
        return
    if settings.use_mock_events:
        providers = [MockEventProvider()]
    else:
        providers = [TheNewsApiProvider(settings)]
    svc = EventAnalysisService(db, settings)
    import asyncio

    for prov in providers:
        for pkt in prov.poll()[:2]:
            row, err = asyncio.run(svc.analyze_and_persist(pkt))
            if err:
                log.debug("event skip: %s", err)
            else:
                log.info("event analysis id=%s", getattr(row, "id", None))
