from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.market_snapshot import MarketSnapshot
from app.services.market_data.chain_contract_proxy import best_effort_option_contract
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
        now_ts = utc_now().timestamp()
        extra: dict = {}
        if tick and (bid is not None or ask is not None or underlying is not None):
            extra["quote_ts_epoch"] = now_ts
            if tick.raw and isinstance(tick.raw, dict):
                et = tick.raw.get("eventTime") or tick.raw.get("event_time")
                if et is not None:
                    try:
                        extra["quote_ts_epoch"] = float(et) / 1000.0
                    except (TypeError, ValueError):
                        pass

        try:
            chain = await self._chains.fetch_chain(symbol)
            extra["chain_liquidity"] = OptionChainService.liquidity_proxy(chain)
            extra["chain_mock"] = chain.get("mock", False)
            extra["chain_ts_epoch"] = now_ts
            proxy = best_effort_option_contract(chain, underlying)
            if proxy:
                extra["option_contract"] = proxy
            extra["api_degraded"] = False
        except Exception as e:
            extra["chain_error"] = str(e)[:200]
            extra["api_degraded"] = True
            extra["chain_ts_epoch"] = 0.0

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
