#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
import csv
from decimal import Decimal
from pathlib import Path

from polybot.backtesting import BacktestConfig, BacktestEngine
from polybot.core.config import get_settings
from polybot.data.normalization.time import normalize_datetime
from polybot.data.storage.database import create_session_factory
from polybot.data.storage.mappers import orderbook_snapshot_from_orm
from polybot.data.storage.repositories import OrderBookRepository
from polybot.knowledge.obsidian import ObsidianVault
from polybot.obsidian.reports import render_backtest_result_report
from polybot.strategies.research import get_research_strategy


async def run() -> int:
    parser = argparse.ArgumentParser(description="Run a research-only backtest over stored snapshots.")
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--market-id", required=True)
    parser.add_argument("--from", dest="from_date")
    parser.add_argument("--to", dest="to_date")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--initial-cash", default="1000")
    parser.add_argument("--order-size", default="10")
    parser.add_argument("--fee-bps", default="0")
    parser.add_argument("--latency-ms", type=int, default=500)
    parser.add_argument("--json-out", type=Path, default=Path("tmp/backtest_result.json"))
    parser.add_argument("--csv-out", type=Path, default=Path("tmp/backtest_trades.csv"))
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

    strategy = get_research_strategy(args.strategy)
    config = BacktestConfig(
        strategy_name=args.strategy,
        market_id=args.market_id,
        initial_cash=Decimal(args.initial_cash),
        order_size=Decimal(args.order_size),
        fee_bps=Decimal(args.fee_bps),
        latency_ms=args.latency_ms,
    )
    result = BacktestEngine(config).run(strategy=strategy, snapshots=snapshots)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(result.to_json() + "\n", encoding="utf-8")

    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    with args.csv_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["order_id", "asset_id", "side", "requested_size", "filled_size", "average_price", "fees", "slippage", "filled_at", "partial", "reason", "net_pnl"],
        )
        writer.writeheader()
        for trade in result.trades:
            writer.writerow(
                {
                    "order_id": trade.order.order_id,
                    "asset_id": trade.fill.asset_id,
                    "side": trade.fill.side,
                    "requested_size": trade.fill.requested_size,
                    "filled_size": trade.fill.filled_size,
                    "average_price": trade.fill.average_price,
                    "fees": trade.fill.fees,
                    "slippage": trade.fill.slippage,
                    "filled_at": trade.fill.filled_at.isoformat(),
                    "partial": trade.fill.partial,
                    "reason": trade.order.reason,
                    "net_pnl": trade.net_pnl,
                }
            )

    print(f"Backtest {result.strategy_id} market={result.market_id}")
    print(f"Trades={result.trade_count} NetPnL={result.net_pnl} FillRate={result.fill_rate}")
    print(f"JSON={args.json_out} CSV={args.csv_out}")

    if args.obsidian:
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()
        path = vault.write_note(
            "Backtests",
            f"Backtest Result - {result.strategy_id} - {args.market_id}",
            render_backtest_result_report(result),
            overwrite=True,
        )
        print(f"Obsidian={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))

