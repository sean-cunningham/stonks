from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NormalizedEventPacket(BaseModel):
    """Canonical event shape fed to AI — no browsing, app-supplied fields only."""

    source: str
    event_kind: str
    symbol: str
    headline: str
    body: str | None = None
    occurred_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    dedupe_key: str = Field(min_length=4, max_length=256)
