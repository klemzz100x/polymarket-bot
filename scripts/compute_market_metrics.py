#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
import csv
import json
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
from polybot.knowledge.obsidian import ObsidianVault
from polybot.obsidian.reports import render_market_metrics_report
from polybot.research.metrics import compute_market_metrics_summary, compute_orderbook_metrics


async def run() -> int:
    parser = argparse.ArgumentParser(description="Compute market metrics from stored data.")
    parser.add_argument("--market-id", required=True)
    parser.add_argument("--from", dest="from_date")
    parser.add_argument("--to", dest="to_date")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--json-out", type=Path, default=Path("tmp/market_metrics.json"))
    parser.add_argument("--csv-out", type=Path, default=Path("tmp/orderbook_metrics.csv"))
    parser.add_argument("--obsidian", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    start = normalize_datetime(args.from_date)
    end = normalize_datetime(args.to_date)
    session_factory = create_session_factory(settings.database_url)
    async with session_factory() as session:
        snapshots = [
            orderbook_snapshot_from_orm(row)
            for row in await OrderBookRepository(session).list_snapshots(
                condition_id=args.market_id,
                start=start,
                end=end,
                limit=args.limit,
            )
        ]
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

    summary = compute_market_metrics_summary(
        market_id=args.market_id,
        snapshots=snapshots,
        trades=trades,
        price_ticks=ticks,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(summary.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    with args.csv_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp",
                "asset_id",
                "best_bid",
                "best_ask",
                "mid_price",
                "spread_abs",
                "spread_pct",
                "bid_depth",
                "ask_depth",
                "imbalance",
                "liquidity_score",
            ],
        )
        writer.writeheader()
        for snapshot in snapshots:
            metric = compute_orderbook_metrics(snapshot)
            writer.writerow(
                {
                    "timestamp": snapshot.snapshot_ts.isoformat(),
                    "asset_id": snapshot.asset_id,
                    "best_bid": metric.best_bid,
                    "best_ask": metric.best_ask,
                    "mid_price": metric.mid_price,
                    "spread_abs": metric.spread_abs,
                    "spread_pct": metric.spread_pct,
                    "bid_depth": metric.bid_depth,
                    "ask_depth": metric.ask_depth,
                    "imbalance": metric.orderbook_imbalance,
                    "liquidity_score": metric.liquidity_score,
                }
            )

    print(f"Metrics for {args.market_id}")
    print(f"Snapshots={summary.snapshot_count} Trades={summary.trade_count} Ticks={summary.price_tick_count}")
    print(f"Avg spread={summary.average_spread_abs} Liquidity score={summary.liquidity_score}")
    print(f"JSON={args.json_out} CSV={args.csv_out}")

    if args.obsidian:
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()
        path = vault.write_note(
            "Market-Research",
            f"Market Metrics Report - {args.market_id}",
            render_market_metrics_report(summary),
            overwrite=True,
        )
        print(f"Obsidian={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))

