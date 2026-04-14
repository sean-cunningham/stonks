from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.market_snapshot import MarketSnapshot
from app.services.market_data.option_chain_service import OptionChainService
from app.services.market_data.quote_cache import QuoteCache


class MarketSnapshotService:
    def __init__(
        self,
        db: Session,
        quotes: QuoteCache,
        chains: OptionChainService,
    ) -> None:
        self._db = db
        self._quotes = quotes
        self._chains = chains

    async def build_and_persist(self, symbol: str) -> MarketSnapshot:
        tick = self._quotes.get(symbol)
        spread_bps = self._quotes.spread_bps(symbol)
        underlying = None
        bid = ask = vol = None
        if tick:
            bid, ask = tick.bid, tick.ask
            underlying = tick.last or (
                (tick.bid + tick.ask) / 2 if tick.bid and tick.ask else None
            )
            vol = tick.volume
        extra: dict = {}
        try:
            chain = await self._chains.fetch_chain(symbol)
            extra["chain_liquidity"] = OptionChainService.liquidity_proxy(chain)
            extra["chain_mock"] = chain.get("mock", False)
        except Exception as e:
            extra["chain_error"] = str(e)[:200]

        snap = MarketSnapshot(
            symbol=symbol.upper(),
            created_at=utc_now(),
            underlying_price=underlying,
            bid=bid,
            ask=ask,
            volume=vol,
            spread_bps=spread_bps,
            extra=extra,
        )
        self._db.add(snap)
        self._db.commit()
        self._db.refresh(snap)
        return snap
