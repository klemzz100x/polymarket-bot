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
from polybot.paper_trading import PaperTradingConfig
from polybot.shadow_trading import ShadowTradingEngine
from polybot.shadow_trading.reporting import render_shadow_trading_report
from polybot.shadow_trading.storage import ShadowTradingRepository


async def run() -> int:
    parser = argparse.ArgumentParser(description="Run shadow trading without sending real orders.")
    parser.add_argument("--market-id", required=True)
    parser.add_argument("--strategy", default="wide-spread-mean-reversion")
    parser.add_argument("--from", dest="from_date")
    parser.add_argument("--to", dest="to_date")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--initial-cash", default="1000")
    parser.add_argument("--order-size", default="10")
    parser.add_argument("--max-position", default="100")
    parser.add_argument("--max-market-exposure", default="250")
    parser.add_argument("--fee-bps", default="0")
    parser.add_argument("--latency-ms", type=int, default=500)
    parser.add_argument("--signal-window", type=int, default=20)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--persist-db", action="store_true")
    parser.add_argument("--obsidian", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    run_id = str(uuid.uuid4())
    json_out = args.json_out or Path("tmp/shadow_trading") / f"{run_id}.json"
    session_factory = create_session_factory(settings.database_url)

    async with session_factory() as session:
        snapshots = [
            orderbook_snapshot_from_orm(row)
            for row in await OrderBookRepository(session).list_snapshots(
                condition_id=args.market_id,
                start=normalize_datetime(args.from_date),
                end=normalize_datetime(args.to_date),
                limit=args.limit,
            )
        ]
        trades = [
            trade_from_orm(row)
            for row in await TradeRepository(session).list_trades(
                condition_id=args.market_id,
                start=normalize_datetime(args.from_date),
                end=normalize_datetime(args.to_date),
                limit=args.limit,
            )
        ]

        result = ShadowTradingEngine(
            PaperTradingConfig(
                market_id=args.market_id,
                strategy_name=args.strategy,
                run_id=run_id,
                initial_cash=Decimal(args.initial_cash),
                order_size=Decimal(args.order_size),
                max_position=Decimal(args.max_position),
                max_market_exposure=Decimal(args.max_market_exposure),
                fee_bps=Decimal(args.fee_bps),
                latency_ms=args.latency_ms,
                signal_window=args.signal_window,
                decision_mode="signals",
            )
        ).run(snapshots=snapshots, trades=trades)

        if args.persist_db:
            await ShadowTradingRepository(session).insert_result(result)
            await session.commit()

    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(result.to_json() + "\n", encoding="utf-8")

    print(f"Shadow run={result.run_id} strategy={result.strategy_name}")
    print(f"Snapshots={result.snapshot_count} Signals={result.signal_count}")
    print(
        "Decisions="
        f"{result.decision_count} Fills={result.theoretical_fill_count} "
        f"Missed={result.missed_fill_count} Impossible={result.impossible_fill_count}"
    )
    print(f"AvgSlippage={result.average_slippage} FillProbability={result.fill_probability}")
    print(f"JSON={json_out}")

    if args.obsidian:
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()
        path = vault.write_note(
            "Shadow-Trading",
            f"Shadow Trading Daily Report - {result.strategy_name} - {args.market_id}",
            render_shadow_trading_report(result),
            overwrite=True,
        )
        print(f"Obsidian={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
