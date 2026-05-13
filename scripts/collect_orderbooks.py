#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio

from redis.asyncio import Redis

from polybot.core.config import get_settings
from polybot.core.logging import configure_logging
from polybot.data.ingestion import PolymarketDataCollector
from polybot.data.storage.database import create_session_factory
from polybot.data.storage.repositories import MarketRepository
from polybot.polymarket.api import PolymarketClient


async def run() -> int:
    parser = argparse.ArgumentParser(description="Collect Polymarket CLOB orderbook snapshots.")
    parser.add_argument("--token-id", action="append", dest="token_ids", default=[])
    parser.add_argument("--market-id")
    parser.add_argument("--active-limit", type=int)
    parser.add_argument("--interval", type=float, default=None)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-redis", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)
    interval = args.interval or settings.polymarket_default_orderbook_interval_seconds

    session_factory = create_session_factory(settings.database_url)
    redis = None if args.no_redis else Redis.from_url(settings.redis_url)
    total = 0

    async with PolymarketClient(settings) as client:
        async with session_factory() as session:
            token_ids = list(args.token_ids)
            if args.market_id:
                token_ids.extend(await MarketRepository(session).asset_ids_for_market(args.market_id))
            if args.active_limit and not token_ids:
                token_ids.extend(await MarketRepository(session).active_asset_ids(limit=args.active_limit))
            if not token_ids:
                raise SystemExit("Provide --token-id, --market-id, or --active-limit after collecting markets.")

            collector = PolymarketDataCollector(
                client=client,
                session=None if args.dry_run else session,
                redis=redis,
            )
            for index in range(args.iterations):
                snapshots = await collector.collect_orderbooks(
                    token_ids=token_ids,
                    persist=not args.dry_run,
                )
                total += len(snapshots)
                if index < args.iterations - 1:
                    await asyncio.sleep(interval)

    if redis:
        await redis.aclose()
    print(f"Collected {total} orderbook snapshots. dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))

