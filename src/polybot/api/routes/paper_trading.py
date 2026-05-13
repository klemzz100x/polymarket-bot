from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from polybot.core.config import Settings, get_settings
from polybot.core.logging import get_logger
from polybot.core.security import verify_automation_secret
from polybot.data.normalization.time import normalize_datetime
from polybot.data.storage.database import create_session_factory
from polybot.data.storage.mappers import orderbook_snapshot_from_orm, trade_from_orm
from polybot.data.storage.repositories import OrderBookRepository, TradeRepository
from polybot.knowledge.obsidian import ObsidianVault
from polybot.monitoring import record_paper_trading_result
from polybot.obsidian.reports import render_paper_trading_report
from polybot.paper_trading import PaperTradingConfig, PaperTradingEngine
from polybot.paper_trading.equity_storage import PaperEquityRepository
from polybot.paper_trading.storage import PaperTradingRepository
from polybot.strategies.research import get_research_strategy

router = APIRouter(prefix="/paper-trading", tags=["paper-trading"], dependencies=[Depends(verify_automation_secret)])
logger = get_logger(__name__)


class PaperTradingRunRequest(BaseModel):
    market_id: str
    strategy: str = "wide-spread-mean-reversion"
    decision_mode: str = Field(default="hybrid", pattern="^(strategy|signals|hybrid)$")
    start: str | None = None
    end: str | None = None
    limit: int = Field(default=5000, ge=1, le=50000)
    initial_cash: str = "1000"
    order_size: str = "10"
    fee_bps: str = "0"
    latency_ms: int = 500
    signal_window: int = 20
    persist_db: bool = False
    write_obsidian: bool = False


class PaperTradingEquityRequest(BaseModel):
    market_id: str | None = None
    strategy: str | None = None
    start: str | None = None
    end: str | None = None
    limit: int = Field(default=1000, ge=1, le=10000)


@router.post("/run")
async def run_paper_trading(
    request: PaperTradingRunRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    run_id = str(uuid4())
    start = normalize_datetime(request.start)
    end = normalize_datetime(request.end)
    ledger_path = Path("logs/paper-trading") / f"{run_id}.jsonl"
    session_factory = create_session_factory(settings.database_url)

    async with session_factory() as session:
        snapshots = [
            orderbook_snapshot_from_orm(row)
            for row in await OrderBookRepository(session).list_snapshots(
                condition_id=request.market_id,
                start=start,
                end=end,
                limit=request.limit,
            )
        ]
        trades = [
            trade_from_orm(row)
            for row in await TradeRepository(session).list_trades(
                condition_id=request.market_id,
                start=start,
                end=end,
                limit=request.limit,
            )
        ]
        strategy = None if request.decision_mode == "signals" else get_research_strategy(request.strategy)
        result = PaperTradingEngine(
            PaperTradingConfig(
                market_id=request.market_id,
                strategy_name=request.strategy,
                run_id=run_id,
                initial_cash=Decimal(request.initial_cash),
                order_size=Decimal(request.order_size),
                fee_bps=Decimal(request.fee_bps),
                latency_ms=request.latency_ms,
                signal_window=request.signal_window,
                decision_mode=request.decision_mode,
                ledger_path=str(ledger_path),
            ),
            strategy=strategy,
        ).run(snapshots=snapshots, trades=trades)
        record_paper_trading_result(result)

        if request.persist_db:
            await PaperTradingRepository(session).insert_result(result)
            await session.commit()

    note = None
    if request.write_obsidian:
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()
        note = str(
            vault.write_note(
                "Paper-Trading",
                f"Paper Trading Report - {result.strategy_name} - {request.market_id}",
                render_paper_trading_report(result),
                overwrite=True,
            )
        )

    logger.info("paper_trading_run_completed", run_id=run_id, market_id=request.market_id)
    return {
        "job_id": run_id,
        "status": "completed",
        "ledger": str(ledger_path),
        "note": note,
        "result": result.to_dict(),
    }


@router.get("/equity")
async def get_paper_trading_equity(
    market_id: str | None = None,
    strategy: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = 1000,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    request = PaperTradingEquityRequest(
        market_id=market_id,
        strategy=strategy,
        start=start,
        end=end,
        limit=limit,
    )
    session_factory = create_session_factory(settings.database_url)
    async with session_factory() as session:
        repo = PaperEquityRepository(session)
        latest = await repo.latest_equity(
            strategy_name=request.strategy,
            market_id=request.market_id,
        )
        history = await repo.list_equity(
            strategy_name=request.strategy,
            market_id=request.market_id,
            start=normalize_datetime(request.start),
            end=normalize_datetime(request.end),
            limit=request.limit,
        )
    return {
        "status": "ok",
        "latest": _json_ready(latest),
        "history": _json_ready(history),
    }


@router.get("/performance/live")
async def get_live_paper_trading_performance(
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    session_factory = create_session_factory(settings.database_url)
    async with session_factory() as session:
        performance = await PaperEquityRepository(session).live_performance()
    return {"status": "ok", "performance": _json_ready(performance)}


def _json_ready(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    return value
