from typing import Any

from app.services.market_data.broker_adapter import BrokerAdapter


class OptionChainService:
    def __init__(self, broker: BrokerAdapter) -> None:
        self._broker = broker

    async def fetch_chain(self, symbol: str) -> dict[str, Any]:
        return await self._broker.get_option_chain(symbol)

    @staticmethod
    def liquidity_proxy(chain: dict[str, Any]) -> dict[str, float | None]:
        """Derive simple liquidity metrics without full NBBO per strike."""
        strikes = chain.get("strikes") or chain.get("data", {}).get("items")
        n = len(strikes) if isinstance(strikes, list) else 0
        return {
            "strike_count": float(n),
            "open_interest_proxy": float(n) if n else None,
        }
