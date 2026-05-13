"""Data collection jobs for Polymarket read-only data."""

from typing import Any

__all__ = ["MarketDataSource", "MarketEvent", "MarketEventIngestor", "PolymarketDataCollector"]


def __getattr__(name: str) -> Any:
    if name == "PolymarketDataCollector":
        from polybot.data.ingestion.collectors import PolymarketDataCollector

        return PolymarketDataCollector
    if name in {"MarketDataSource", "MarketEvent", "MarketEventIngestor"}:
        from polybot.data.ingestion.events import MarketDataSource, MarketEvent, MarketEventIngestor

        return {
            "MarketDataSource": MarketDataSource,
            "MarketEvent": MarketEvent,
            "MarketEventIngestor": MarketEventIngestor,
        }[name]
    raise AttributeError(name)
