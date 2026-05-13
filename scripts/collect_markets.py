#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio

from redis.asyncio import Redis

from polybot.core.config import get_settings
from polybot.core.logging import configure_logging
from polybot.data.ingestion import PolymarketDataCollector
from polybot.data.storage.database import create_session_factory
from polybot.polymarket.api import PolymarketClient


async def run() -> int:
    parser = argparse.ArgumentParser(description="Collect Polymarket market metadata.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--active", action="store_true", default=True)
    parser.add_argument("--include-closed", action="store_true")
    parser.add_argument("--orderbook-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-redis", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)

    session_factory = create_session_factory(settings.database_url)
    redis = None if args.no_redis else Redis.from_url(settings.redis_url)

    async with PolymarketClient(settings) as client:
        if args.dry_run:
            collector = PolymarketDataCollector(client=client, session=None, redis=redis)
            markets = await collector.collect_markets(
                active=args.active,
                closed=None if args.include_closed else False,
                limit=args.limit,
                offset=args.offset,
                enable_order_book=True if args.orderbook_only else None,
                persist=False,
            )
        else:
            async with session_factory() as session:
                collector = PolymarketDataCollector(client=client, session=session, redis=redis)
                markets = await collector.collect_markets(
                    active=args.active,
                    closed=None if args.include_closed else False,
                    limit=args.limit,
                    offset=args.offset,
                    enable_order_book=True if args.orderbook_only else None,
                    persist=True,
                )

    if redis:
        await redis.aclose()
    print(f"Collected {len(markets)} markets. dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))

