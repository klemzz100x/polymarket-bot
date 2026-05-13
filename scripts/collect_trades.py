#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio

from polybot.core.config import get_settings
from polybot.core.logging import configure_logging
from polybot.data.ingestion import PolymarketDataCollector
from polybot.data.storage.database import create_session_factory
from polybot.polymarket.api import PolymarketClient


async def run() -> int:
    parser = argparse.ArgumentParser(description="Collect public Polymarket trades from Data API.")
    parser.add_argument("--market-id", action="append", dest="market_ids", default=[])
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)
    session_factory = create_session_factory(settings.database_url)

    async with PolymarketClient(settings) as client:
        if args.dry_run:
            collector = PolymarketDataCollector(client=client, session=None)
            trades = await collector.collect_trades(
                markets=args.market_ids or None,
                limit=args.limit,
                offset=args.offset,
                persist=False,
            )
        else:
            async with session_factory() as session:
                collector = PolymarketDataCollector(client=client, session=session)
                trades = await collector.collect_trades(
                    markets=args.market_ids or None,
                    limit=args.limit,
                    offset=args.offset,
                    persist=True,
                )

    print(f"Collected {len(trades)} public trades. dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))

