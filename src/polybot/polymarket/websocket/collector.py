from collections.abc import Sequence
from typing import Any

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from polybot.core.logging import get_logger
from polybot.data.normalization import normalize_orderbook, normalize_public_trade
from polybot.data.normalization.time import utc_now
from polybot.data.storage.redis_cache import MarketRedisCache
from polybot.data.storage.repositories import OrderBookRepository, RawPayloadRepository, TradeRepository
from polybot.polymarket.websocket.client import PolymarketMarketWebsocket

logger = get_logger(__name__)


class PolymarketWebsocketCollector:
    def __init__(
        self,
        websocket: PolymarketMarketWebsocket,
        *,
        session: AsyncSession | None = None,
        redis: Redis | None = None,
    ) -> None:
        self.websocket = websocket
        self.session = session
        self.cache = MarketRedisCache(redis) if redis else None

    async def stream_orderbooks(
        self,
        *,
        asset_ids: Sequence[str],
        max_messages: int | None = None,
    ) -> int:
        count = 0
        async for event in self.websocket.stream_orderbooks(asset_ids):
            events = _flatten_events(event)
            for raw_event in events:
                await self._handle_orderbook_event(raw_event)
                count += 1
                if max_messages is not None and count >= max_messages:
                    return count
        return count

    async def stream_trades(
        self,
        *,
        asset_ids: Sequence[str],
        max_messages: int | None = None,
    ) -> int:
        count = 0
        async for event in self.websocket.stream_trades(asset_ids):
            events = _flatten_events(event)
            for raw_event in events:
                await self._handle_trade_event(raw_event)
                count += 1
                if max_messages is not None and count >= max_messages:
                    return count
        return count

    async def _handle_orderbook_event(self, raw_event: dict[str, Any]) -> None:
        if self.session:
            await RawPayloadRepository(self.session).insert_many(
                source="polymarket_clob_ws",
                endpoint="/ws/market",
                payloads=[raw_event],
                external_id_key="asset_id",
            )
        if not {"bids", "asks"} <= raw_event.keys():
            if self.session:
                await self.session.commit()
            return

        snapshot = normalize_orderbook(raw_event, received_at=utc_now())
        if self.session:
            await OrderBookRepository(self.session).insert_many([snapshot])
            await self.session.commit()
        if self.cache:
            await self.cache.cache_orderbook(snapshot)
        logger.info("polymarket_ws_orderbook_stored", asset_id=snapshot.asset_id)

    async def _handle_trade_event(self, raw_event: dict[str, Any]) -> None:
        if self.session:
            await RawPayloadRepository(self.session).insert_many(
                source="polymarket_clob_ws",
                endpoint="/ws/market",
                payloads=[raw_event],
                external_id_key="id",
            )
        if not {"price", "size"} <= raw_event.keys():
            if self.session:
                await self.session.commit()
            return

        trade = normalize_public_trade(raw_event)
        if self.session:
            await TradeRepository(self.session).upsert_many([trade])
            await self.session.commit()
        logger.info("polymarket_ws_trade_stored", trade_id=trade.trade_id)


def _flatten_events(event: dict[str, Any]) -> list[dict[str, Any]]:
    events = event.get("events")
    if isinstance(events, list):
        return [item for item in events if isinstance(item, dict)]
    return [event]
