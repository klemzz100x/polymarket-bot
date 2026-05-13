#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
import csv
from pathlib import Path

from polybot.core.config import get_settings
from polybot.data.normalization.time import normalize_datetime
from polybot.data.storage.database import create_session_factory
from polybot.data.storage.mappers import orderbook_snapshot_from_orm, trade_from_orm
from polybot.data.storage.repositories import OrderBookRepository, TradeRepository
from polybot.knowledge.obsidian import ObsidianVault
from polybot.obsidian.reports import render_inefficiency_scan_report
from polybot.research.inefficiencies import scan_inefficiencies


async def run() -> int:
    parser = argparse.ArgumentParser(description="Scan stored market data for simple inefficiencies.")
    parser.add_argument("--market-id", required=True)
    parser.add_argument("--from", dest="from_date")
    parser.add_argument("--to", dest="to_date")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--json-out", type=Path, default=Path("tmp/inefficiency_scan.json"))
    parser.add_argument("--csv-out", type=Path, default=Path("tmp/inefficiency_scan.csv"))
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

    report = scan_inefficiencies(market_id=args.market_id, snapshots=snapshots, trades=trades)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(report.to_json() + "\n", encoding="utf-8")
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    with args.csv_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["market_id", "asset_id", "timestamp", "signal_type", "severity", "confidence", "description", "hypothesis", "next_action"],
        )
        writer.writeheader()
        for signal in report.signals:
            writer.writerow(
                {
                    "market_id": signal.market_id,
                    "asset_id": signal.asset_id,
                    "timestamp": signal.timestamp.isoformat(),
                    "signal_type": signal.signal_type,
                    "severity": signal.severity,
                    "confidence": signal.confidence,
                    "description": signal.description,
                    "hypothesis": signal.hypothesis,
                    "next_action": signal.next_action,
                }
            )
    print(f"Signals={report.signal_count} JSON={args.json_out} CSV={args.csv_out}")

    if args.obsidian:
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()
        path = vault.write_note(
            "Research/Inefficiencies",
            f"Inefficiency Scan Report - {args.market_id}",
            render_inefficiency_scan_report(report),
            overwrite=True,
        )
        print(f"Obsidian={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))

