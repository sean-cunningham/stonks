from typing import Any, Protocol


class BrokerAdapter(Protocol):
    """Abstract tastytrade (or future broker) connectivity."""

    async def refresh_oauth_if_needed(self) -> None:
        ...

    async def get_dxlink_token(self) -> dict[str, Any]:
        """Return payload containing streamer token and metadata (shape varies by broker)."""
        ...

    async def get_option_chain(self, symbol: str) -> dict[str, Any]:
        ...
