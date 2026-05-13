"""Public Polymarket websocket adapters."""
"""Polymarket WebSocket client and collector."""

from typing import Any

from polybot.polymarket.websocket.client import (
    PolymarketMarketWebsocket,
    WebsocketConfig,
    build_market_subscription,
    parse_websocket_message,
)

__all__ = [
    "PolymarketMarketWebsocket",
    "PolymarketWebsocketCollector",
    "WebsocketConfig",
    "build_market_subscription",
    "parse_websocket_message",
]


def __getattr__(name: str) -> Any:
    if name == "PolymarketWebsocketCollector":
        from polybot.polymarket.websocket.collector import PolymarketWebsocketCollector

        return PolymarketWebsocketCollector
    raise AttributeError(name)
