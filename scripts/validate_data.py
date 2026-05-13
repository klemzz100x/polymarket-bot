#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from polybot.core.config import get_settings
from polybot.data.normalization.time import normalize_datetime
from polybot.data.storage.database import create_session_factory
from polybot.data.storage.mappers import orderbook_snapshot_from_orm, price_tick_from_orm, trade_from_orm
from polybot.data.storage.repositories import (
    MarketRepository,
    OrderBookRepository,
    PriceTickRepository,
    TradeRepository,
)
from polybot.data.validation import validate_market_dataset
from polybot.knowledge.obsidian import ObsidianVault
from polybot.obsidian.reports import render_data_quality_report


async def run() -> int:
    parser = argparse.ArgumentParser(description="Validate collected Polymarket data quality.")
    parser.add_argument("--market-id", required=True)
    parser.add_argument("--from", dest="from_date")
    parser.add_argument("--to", dest="to_date")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--json-out", type=Path, default=Path("tmp/data_quality_report.json"))
    parser.add_argument("--obsidian", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    start = normalize_datetime(args.from_date)
    end = normalize_datetime(args.to_date)
    session_factory = create_session_factory(settings.database_url)

    async with session_factory() as session:
        snapshot_rows = await OrderBookRepository(session).list_snapshots(
            condition_id=args.market_id,
            start=start,
            end=end,
            limit=args.limit,
        )
        snapshots = [orderbook_snapshot_from_orm(row) for row in snapshot_rows]
        trades = [
            trade_from_orm(row)
            for row in await TradeRepository(session).list_trades(
                condition_id=args.market_id,
                start=start,
                end=end,
                limit=args.limit,
            )
        ]
        asset_ids = await MarketRepository(session).asset_ids_for_market(args.market_id)
        if not asset_ids:
            asset_ids = sorted({snapshot.asset_id for snapshot in snapshots})
        ticks = []
        for asset_id in asset_ids:
            ticks.extend(
                price_tick_from_orm(row)
                for row in await PriceTickRepository(session).list_ticks(
                    asset_id=asset_id,
                    start=start,
                    end=end,
                    limit=args.limit,
                )
            )

    report = validate_market_dataset(
        market_id=args.market_id,
        snapshots=snapshots,
        trades=trades,
        price_ticks=ticks,
        expected_interval_seconds=settings.polymarket_default_orderbook_interval_seconds,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(report.to_json() + "\n", encoding="utf-8")

    print(f"Data quality status: {report.status}")
    print(f"Snapshots={report.snapshot_count} Trades={report.trade_count} Ticks={report.price_tick_count}")
    print(f"Issues={len(report.issues)} JSON={args.json_out}")

    if args.obsidian:
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()
        path = vault.write_note(
            "Data",
            f"Data Quality Report - {args.market_id}",
            render_data_quality_report(report),
            overwrite=True,
        )
        print(f"Obsidian={path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))

