#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
from decimal import Decimal
from pathlib import Path
import uuid

from polybot.core.config import get_settings
from polybot.data.normalization.time import normalize_datetime
from polybot.data.storage.database import create_session_factory
from polybot.data.storage.mappers import orderbook_snapshot_from_orm, trade_from_orm
from polybot.data.storage.repositories import OrderBookRepository, TradeRepository
from polybot.knowledge.obsidian import ObsidianVault
from polybot.obsidian.reports import render_paper_trading_report
from polybot.paper_trading import PaperTradingConfig, PaperTradingEngine
from polybot.paper_trading.storage import PaperTradingRepository
from polybot.strategies.research import get_research_strategy


async def run() -> int:
    parser = argparse.ArgumentParser(description="Run a research-only paper trading simulation.")
    parser.add_argument("--market-id", required=True)
    parser.add_argument("--strategy", default="wide-spread-mean-reversion")
    parser.add_argument("--decision-mode", choices=["strategy", "signals", "hybrid"], default="hybrid")
    parser.add_argument("--from", dest="from_date")
    parser.add_argument("--to", dest="to_date")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--initial-cash", default="1000")
    parser.add_argument("--order-size", default="10")
    parser.add_argument("--fee-bps", default="0")
    parser.add_argument("--latency-ms", type=int, default=500)
    parser.add_argument("--signal-window", type=int, default=20)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--ledger-out", type=Path)
    parser.add_argument("--persist-db", action="store_true")
    parser.add_argument("--obsidian", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    run_id = str(uuid.uuid4())
    ledger_path = args.ledger_out or Path("logs/paper-trading") / f"{run_id}.jsonl"
    json_out = args.json_out or Path("tmp/paper_trading") / f"{run_id}.json"
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

        strategy = None if args.decision_mode == "signals" else get_research_strategy(args.strategy)
        result = PaperTradingEngine(
            PaperTradingConfig(
                market_id=args.market_id,
                strategy_name=args.strategy,
                run_id=run_id,
                initial_cash=Decimal(args.initial_cash),
                order_size=Decimal(args.order_size),
                fee_bps=Decimal(args.fee_bps),
                latency_ms=args.latency_ms,
                signal_window=args.signal_window,
                decision_mode=args.decision_mode,
                ledger_path=str(ledger_path),
            ),
            strategy=strategy,
        ).run(snapshots=snapshots, trades=trades)

        if args.persist_db:
            await PaperTradingRepository(session).insert_result(result)
            await session.commit()

    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(result.to_json() + "\n", encoding="utf-8")

    print(f"Paper run={result.run_id} mode={args.decision_mode} strategy={result.strategy_name}")
    print(f"Snapshots={result.snapshot_count} Signals={result.signal_count}")
    print(f"Orders={result.attempted_orders} Fills={result.filled_orders} Rejected={result.rejected_orders}")
    print(f"NetPnL={result.net_pnl} FinalEquity={result.final_equity}")
    print(f"JSON={json_out} Ledger={ledger_path}")

    if args.obsidian:
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()
        path = vault.write_note(
            "Paper-Trading",
            f"Paper Trading Report - {result.strategy_name} - {args.market_id}",
            render_paper_trading_report(result),
            overwrite=True,
        )
        print(f"Obsidian={path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
