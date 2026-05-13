from collections.abc import AsyncIterator, Protocol
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class MarketEvent:
    market_id: str
    event_type: str
    received_at: datetime
    payload: dict[str, object]


class MarketDataSource(Protocol):
    def stream(self) -> AsyncIterator[MarketEvent]:
        ...


class MarketEventIngestor:
    def __init__(self, source: MarketDataSource) -> None:
        self.source = source

    async def events(self) -> AsyncIterator[MarketEvent]:
        async for event in self.source.stream():
            yield event

