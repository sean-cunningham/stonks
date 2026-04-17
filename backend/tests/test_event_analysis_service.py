import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.enums import AppMode
from app.models import Base
from app.services.ai.event_analysis_service import EventAnalysisService
from app.services.events.mock_event_provider import MockEventProvider


@pytest.fixture
def db_sess():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    S = sessionmaker(bind=engine)
    s = S()
    yield s
    s.close()


@pytest.mark.asyncio
async def test_mock_persist(db_sess):
    s = Settings(
        use_mock_openai=True,
        openai_enable_real_calls=False,
        use_mock_xai=True,
        xai_enable_real_calls=False,
        xai_enable_x_search_enrichment=True,
        app_mode=AppMode.MOCK,
    )
    svc = EventAnalysisService(db_sess, s)
    pkt = MockEventProvider().poll()[0]
    row, err = await svc.analyze_and_persist(pkt)
    assert err is None
    assert row is not None
    assert row.symbol == pkt.symbol.upper()


@pytest.mark.asyncio
async def test_provider_guard_blocks_non_openai(db_sess):
    s = Settings(use_mock_openai=True, openai_enable_real_calls=False, app_mode=AppMode.MOCK)
    s.ai_provider = "xai"
    s.openai_enabled = True
    svc = EventAnalysisService(db_sess, s)
    pkt = MockEventProvider().poll()[0]
    row, err = await svc.analyze_and_persist(pkt)
    assert row is None
    assert err is not None
    assert "disabled for v1 runtime" in err
