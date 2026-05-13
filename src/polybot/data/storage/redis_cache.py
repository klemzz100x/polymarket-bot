import json
from collections.abc import Iterable
from typing import Any

from redis.asyncio import Redis

from polybot.data.schemas import Market, OrderBookSnapshot


class MarketRedisCache:
    def __init__(self, redis: Redis, namespace: str = "polybot") -> None:
        self.redis = redis
        self.namespace = namespace

    async def cache_active_markets(self, markets: Iterable[Market], ttl_seconds: int = 300) -> None:
        active = [market for market in markets if market.active and not market.closed]
        key = self._key("markets", "active")
        await self.redis.set(
            key,
            json.dumps([market.model_dump(mode="json") for market in active]),
            ex=ttl_seconds,
        )

    async def get_active_markets(self) -> list[dict[str, Any]]:
        raw = await self.redis.get(self._key("markets", "active"))
        if raw is None:
            return []
        text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else []

    async def cache_orderbook(self, snapshot: OrderBookSnapshot, ttl_seconds: int = 120) -> None:
        key = self._key("orderbook", snapshot.asset_id, "latest")
        await self.redis.set(key, snapshot.model_dump_json(), ex=ttl_seconds)
        await self.redis.publish(self._key("pubsub", "orderbook"), snapshot.model_dump_json())

    async def get_latest_orderbook(self, asset_id: str) -> dict[str, Any] | None:
        raw = await self.redis.get(self._key("orderbook", asset_id, "latest"))
        if raw is None:
            return None
        text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None

    def _key(self, *parts: str) -> str:
        return ":".join((self.namespace, *parts))

