from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.services.market_data.market_snapshot_service import MarketSnapshotService
from app.services.market_data.mock_broker import MockBrokerAdapter
from app.services.market_data.option_chain_service import OptionChainService
from app.services.market_data.quote_cache import QuoteCache, QuoteTick


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
async def test_snapshot_extra_has_timestamps_and_chain_liquidity(db_sess):
    qc = QuoteCache()
    qc.update(QuoteTick(symbol="SPY", bid=500.0, ask=500.1, last=500.05, volume=1e6))
    svc = MarketSnapshotService(db_sess, qc, OptionChainService(MockBrokerAdapter()))
    snap = await svc.build_and_persist("SPY")
    assert snap.symbol == "SPY"
    ex = snap.extra or {}
    assert "quote_ts_epoch" in ex
    assert "chain_ts_epoch" in ex
    assert ex.get("chain_liquidity") is not None
    assert ex.get("api_degraded") is False


@pytest.mark.asyncio
async def test_snapshot_chain_error_sets_degraded_and_stale_chain_ts(db_sess):
    class _BadBroker(MockBrokerAdapter):
        async def get_option_chain(self, symbol: str) -> dict:
            raise RuntimeError("simulated chain failure")

    qc = QuoteCache()
    qc.update(QuoteTick(symbol="QQQ", bid=400.0, ask=400.2, last=400.1, volume=1e5))
    svc = MarketSnapshotService(db_sess, qc, OptionChainService(_BadBroker()))
    snap = await svc.build_and_persist("QQQ")
    ex = snap.extra or {}
    assert ex.get("chain_error")
    assert ex.get("api_degraded") is True
    assert ex.get("chain_ts_epoch") == 0.0
    assert "quote_ts_epoch" in ex
