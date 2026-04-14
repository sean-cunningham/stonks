from typing import Protocol

from app.services.events.normalized_packet import NormalizedEventPacket


class EventProviderBase(Protocol):
    def poll(self) -> list[NormalizedEventPacket]:
        ...
