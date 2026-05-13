from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
import asyncio
import json
from typing import TYPE_CHECKING, Any

try:
    import websockets
except ImportError:  # pragma: no cover - dependency is installed in the app image.
    websockets = None

from polybot.core.logging import get_logger

if TYPE_CHECKING:
    from polybot.core.config import Settings

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class WebsocketConfig:
    reconnect_delay_seconds: float = 1.0
    max_reconnect_delay_seconds: float = 30.0
    reconnect_backoff_multiplier: float = 2.0
    heartbeat_interval_seconds: float = 10.0
    max_reconnects: int | None = None


def build_market_subscription(asset_ids: Sequence[str]) -> dict[str, object]:
    return {"assets_ids": list(asset_ids), "type": "market"}


class PolymarketMarketWebsocket:
    def __init__(self, settings: "Settings", config: WebsocketConfig | None = None) -> None:
        self.settings = settings
        self.config = config or WebsocketConfig()

    @property
    def market_url(self) -> str:
        return f"{self.settings.polymarket_ws_url.rstrip('/')}/market"

    def connect(self):
        if websockets is None:
            raise RuntimeError("websockets dependency is not installed")
        return websockets.connect(
            self.market_url,
            ping_interval=None,
            close_timeout=5,
        )

    async def stream_market_events(
        self,
        asset_ids: Sequence[str],
    ) -> AsyncIterator[dict[str, Any]]:
        if not asset_ids:
            return

        reconnects = 0
        delay = self.config.reconnect_delay_seconds
        subscription = build_market_subscription(asset_ids)

        while self.config.max_reconnects is None or reconnects <= self.config.max_reconnects:
            try:
                async with self.connect() as websocket:
                    await self._subscribe(websocket, subscription)
                    logger.info("polymarket_ws_subscribed", asset_count=len(asset_ids))
                    delay = self.config.reconnect_delay_seconds
                    last_heartbeat = asyncio.get_running_loop().time()

                    async for message in websocket:
                        now = asyncio.get_running_loop().time()
                        if now - last_heartbeat >= self.config.heartbeat_interval_seconds:
                            await self._heartbeat(websocket)
                            last_heartbeat = now

                        parsed = parse_websocket_message(message)
                        if parsed is None:
                            continue
                        yield parsed
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                reconnects += 1
                logger.warning(
                    "polymarket_ws_reconnecting",
                    reconnects=reconnects,
                    delay_seconds=delay,
                    error=str(exc),
                )
                if self.config.max_reconnects is not None and reconnects > self.config.max_reconnects:
                    logger.error("polymarket_ws_reconnects_exhausted", error=str(exc))
                    raise
                await asyncio.sleep(delay)
                delay = min(
                    delay * self.config.reconnect_backoff_multiplier,
                    self.config.max_reconnect_delay_seconds,
                )

    async def stream_orderbooks(
        self,
        asset_ids: Sequence[str],
    ) -> AsyncIterator[dict[str, Any]]:
        async for event in self.stream_market_events(asset_ids):
            for item in _event_items(event):
                event_type = str(item.get("event_type") or item.get("type") or "").lower()
                if event_type in {"book", "orderbook", "price_change"} or {"bids", "asks"} <= item.keys():
                    yield item

    async def stream_trades(
        self,
        asset_ids: Sequence[str],
    ) -> AsyncIterator[dict[str, Any]]:
        async for event in self.stream_market_events(asset_ids):
            for item in _event_items(event):
                event_type = str(item.get("event_type") or item.get("type") or "").lower()
                if event_type in {"trade", "last_trade_price"}:
                    yield item

    async def _subscribe(self, websocket: Any, subscription: dict[str, object]) -> None:
        await websocket.send(json.dumps(subscription))

    async def _heartbeat(self, websocket: Any) -> None:
        try:
            await websocket.send("PING")
        except Exception as exc:
            logger.warning("polymarket_ws_heartbeat_failed", error=str(exc))
            raise


def parse_websocket_message(message: str | bytes) -> dict[str, Any] | None:
    if message in {"PONG", b"PONG"}:
        return None
    if isinstance(message, bytes):
        message = message.decode("utf-8")
    try:
        parsed = json.loads(message)
    except json.JSONDecodeError:
        logger.debug("polymarket_ws_non_json_message", message=message)
        return None
    if isinstance(parsed, dict):
        return parsed
    if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
        return {"events": parsed}
    return None


def _event_items(event: dict[str, Any]) -> list[dict[str, Any]]:
    events = event.get("events")
    if isinstance(events, list):
        return [item for item in events if isinstance(item, dict)]
    return [event]
