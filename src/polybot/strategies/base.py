from collections.abc import Iterable, Protocol

from polybot.data.ingestion import MarketEvent
from polybot.execution.engine import OrderRequest


class Strategy(Protocol):
    strategy_id: str

    def on_event(self, event: MarketEvent) -> Iterable[OrderRequest]:
        ...

