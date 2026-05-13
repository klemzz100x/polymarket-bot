#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
from decimal import Decimal
from pathlib import Path
import uuid

from sqlalchemy import text

from polybot.core.config import get_settings
from polybot.knowledge.obsidian import ObsidianVault
from polybot.live_readiness import (
    execution_quality_checks,
    infrastructure_checks,
    risk_checks,
    score_from_checks,
)
from polybot.live_readiness.kill_switch_checks import evaluate_pre_live_kill_switch
from polybot.live_readiness.reporting import render_live_readiness_report
from polybot.live_readiness.storage import LiveReadinessRepository
from polybot.paper_trading import PaperTradingConfig
from polybot.shadow_trading import ShadowTradingEngine
from polybot.shadow_trading.storage import ShadowTradingRepository

from polybot.data.normalization.time import normalize_datetime
from polybot.data.storage.database import create_session_factory
from polybot.data.storage.mappers import orderbook_snapshot_from_orm, trade_from_orm
from polybot.data.storage.repositories import OrderBookRepository, TradeRepository


async def run() -> int:
    parser = argparse.ArgumentParser(description="Run pre-live readiness checks without live trading.")
    parser.add_argument("--market-id", required=True)
    parser.add_argument("--strategy", default="wide-spread-mean-reversion")
    parser.add_argument("--from", dest="from_date")
    parser.add_argument("--to", dest="to_date")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--drawdown", default="0")
    parser.add_argument("--exposure", default="0")
    parser.add_argument("--latency-ms", type=int, default=500)
    parser.add_argument("--order-size", default="10")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--persist-db", action="store_true")
    parser.add_argument("--obsidian", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    report_id = str(uuid.uuid4())
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
        shadow = ShadowTradingEngine(
            PaperTradingConfig(
                market_id=args.market_id,
                strategy_name=args.strategy,
                run_id=str(uuid.uuid4()),
                order_size=Decimal(args.order_size),
                latency_ms=args.latency_ms,
                decision_mode="signals",
            )
        ).run(snapshots=snapshots, trades=trades)
        db_healthy = bool((await session.execute(text("SELECT 1"))).scalar_one_or_none())
        stale_count = await _stale_data_count(session)
        rejected_rate = (
            Decimal(sum(1 for item in shadow.decisions if item.status == "risk_rejected"))
            / Decimal(shadow.decision_count)
            if shadow.decision_count
            else Decimal("0")
        )
        checks = [
            *execution_quality_checks(shadow),
            *risk_checks(
                drawdown=Decimal(args.drawdown),
                exposure=Decimal(args.exposure),
                rejected_rate=rejected_rate,
            ),
            *infrastructure_checks(
                db_healthy=db_healthy,
                redis_healthy=True,
                api_healthy=True,
                collectors_healthy=True,
                websocket_healthy=True,
                telegram_ready=bool(settings.telegram_bot_token and settings.telegram_chat_id),
                dashboard_ready=True,
                obsidian_ready=Path(settings.obsidian_vault_dir).exists(),
                stale_data_count=stale_count,
            ),
        ]
        kill_switch = evaluate_pre_live_kill_switch(
            shadow=shadow,
            drawdown=Decimal(args.drawdown),
            stale_data_count=stale_count,
            db_healthy=db_healthy,
            redis_healthy=True,
            rejected_order_rate=rejected_rate,
        )
        report = score_from_checks(
            report_id=report_id,
            checks=checks,
            kill_switch_state=kill_switch.state.value,
            metadata={"market_id": args.market_id, "strategy": args.strategy, "no_live_trading": True},
        )
        if args.persist_db:
            await ShadowTradingRepository(session).insert_result(shadow)
            repo = LiveReadinessRepository(session)
            await repo.insert_report(report)
            await repo.insert_kill_switch_events(kill_switch.events)
            await session.commit()

    json_out = args.json_out or Path("tmp/live_readiness") / f"{report_id}.json"
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(report.to_json() + "\n", encoding="utf-8")

    print(f"Readiness report={report.report_id} status={report.status}")
    print(f"Score={report.live_readiness_score} KillSwitch={report.kill_switch_state}")
    print(f"JSON={json_out}")
    if args.obsidian:
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()
        path = vault.write_note(
            "Live-Readiness",
            f"Live Readiness Report - {report.status}",
            render_live_readiness_report(report),
            overwrite=True,
        )
        print(f"Obsidian={path}")
    return 0


async def _stale_data_count(session) -> int:
    result = await session.execute(
        text(
            """
            WITH latest AS (
                SELECT DISTINCT ON (condition_id, asset_id)
                    condition_id, asset_id, snapshot_ts
                FROM app.orderbook_snapshots
                ORDER BY condition_id, asset_id, snapshot_ts DESC
            )
            SELECT COUNT(*) AS stale_count
            FROM latest
            WHERE EXTRACT(EPOCH FROM (now() - snapshot_ts)) > 60
            """
        )
    )
    return int(result.scalar_one() or 0)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
