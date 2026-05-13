from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from polybot.backtesting import BacktestConfig, BacktestEngine
from polybot.core.config import Settings, get_settings
from polybot.core.logging import get_logger
from polybot.core.security import verify_automation_secret
from polybot.data.normalization.time import normalize_datetime
from polybot.data.schemas import OrderBookSnapshot, PriceTick, Trade
from polybot.data.storage.database import create_session_factory
from polybot.data.storage.mappers import (
    orderbook_snapshot_from_orm,
    price_tick_from_orm,
    trade_from_orm,
)
from polybot.data.storage.repositories import (
    MarketRepository,
    OrderBookRepository,
    PriceTickRepository,
    TradeRepository,
)
from polybot.data.validation import validate_market_dataset
from polybot.knowledge.obsidian import ObsidianVault
from polybot.monitoring import record_backtest_result, record_signal_count
from polybot.obsidian.reports import (
    render_backtest_result_report,
    render_data_quality_report,
    render_inefficiency_scan_report,
    render_market_metrics_report,
)
from polybot.research.inefficiencies import scan_inefficiencies
from polybot.research.metrics import compute_market_metrics_summary
from polybot.strategies.research import get_research_strategy

router = APIRouter(dependencies=[Depends(verify_automation_secret)])
logger = get_logger(__name__)


class PeriodRequest(BaseModel):
    market_id: str
    start: str | None = None
    end: str | None = None
    limit: int = Field(default=5000, ge=1, le=50000)
    write_obsidian: bool = False


class BacktestRequest(PeriodRequest):
    strategy: str
    initial_cash: str = "1000"
    order_size: str = "10"
    fee_bps: str = "0"
    latency_ms: int = 500


class GenerateReportRequest(BaseModel):
    folder: str
    title: str
    body: str
    overwrite: bool = False


@router.post("/research/validate-data")
async def validate_data(
    request: PeriodRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    job_id = str(uuid4())
    snapshots, trades, ticks = await _load_dataset(request, settings)
    report = validate_market_dataset(
        market_id=request.market_id,
        snapshots=snapshots,
        trades=trades,
        price_ticks=ticks,
        expected_interval_seconds=settings.polymarket_default_orderbook_interval_seconds,
    )
    note = None
    if request.write_obsidian:
        note = _write_note(
            settings=settings,
            folder="Data",
            title=f"Data Quality Report - {request.market_id}",
            body=render_data_quality_report(report),
        )
    logger.info("research_validate_data_completed", job_id=job_id, market_id=request.market_id)
    return {"job_id": job_id, "status": "completed", "report": report.to_dict(), "note": note}


@router.post("/research/compute-metrics")
async def compute_metrics(
    request: PeriodRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    job_id = str(uuid4())
    snapshots, trades, ticks = await _load_dataset(request, settings)
    summary = compute_market_metrics_summary(
        market_id=request.market_id,
        snapshots=snapshots,
        trades=trades,
        price_ticks=ticks,
    )
    note = None
    if request.write_obsidian:
        note = _write_note(
            settings=settings,
            folder="Market-Research",
            title=f"Market Metrics Report - {request.market_id}",
            body=render_market_metrics_report(summary),
        )
    logger.info("research_compute_metrics_completed", job_id=job_id, market_id=request.market_id)
    return {"job_id": job_id, "status": "completed", "summary": summary.to_dict(), "note": note}


@router.post("/research/scan-inefficiencies")
async def scan_research_inefficiencies(
    request: PeriodRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    job_id = str(uuid4())
    snapshots, trades, _ticks = await _load_dataset(request, settings)
    report = scan_inefficiencies(market_id=request.market_id, snapshots=snapshots, trades=trades)
    record_signal_count(report.signals)
    note = None
    if request.write_obsidian:
        note = _write_note(
            settings=settings,
            folder="Research/Inefficiencies",
            title=f"Inefficiency Scan Report - {request.market_id}",
            body=render_inefficiency_scan_report(report),
        )
    logger.info("research_scan_inefficiencies_completed", job_id=job_id, market_id=request.market_id)
    return {"job_id": job_id, "status": "completed", "report": report.to_dict(), "note": note}


@router.post("/backtesting/run")
async def run_backtest(
    request: BacktestRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    job_id = str(uuid4())
    snapshots, _trades, _ticks = await _load_dataset(request, settings)
    strategy = get_research_strategy(request.strategy)
    result = BacktestEngine(
        BacktestConfig(
            strategy_name=request.strategy,
            market_id=request.market_id,
            initial_cash=Decimal(request.initial_cash),
            order_size=Decimal(request.order_size),
            fee_bps=Decimal(request.fee_bps),
            latency_ms=request.latency_ms,
        )
    ).run(strategy=strategy, snapshots=snapshots)
    record_backtest_result(result)
    note = None
    if request.write_obsidian:
        note = _write_note(
            settings=settings,
            folder="Backtests",
            title=f"Backtest Result - {result.strategy_id} - {request.market_id}",
            body=render_backtest_result_report(result),
        )
    logger.info("backtest_completed", job_id=job_id, strategy=result.strategy_id)
    return {"job_id": job_id, "status": "completed", "result": result.to_dict(), "note": note}


@router.post("/obsidian/generate-report")
async def generate_report(
    request: GenerateReportRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    job_id = str(uuid4())
    note = _write_note(
        settings=settings,
        folder=request.folder,
        title=request.title,
        body=request.body,
        overwrite=request.overwrite,
    )
    logger.info("obsidian_report_generated", job_id=job_id, file=note)
    return {"job_id": job_id, "status": "completed", "note": note}


async def _load_dataset(
    request: PeriodRequest,
    settings: Settings,
) -> tuple[list[OrderBookSnapshot], list[Trade], list[PriceTick]]:
    start = normalize_datetime(request.start)
    end = normalize_datetime(request.end)
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
        asset_ids = await MarketRepository(session).asset_ids_for_market(request.market_id)
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
                    limit=request.limit,
                )
            )
    return snapshots, trades, ticks


def _write_note(
    *,
    settings: Settings,
    folder: str,
    title: str,
    body: str,
    overwrite: bool = True,
) -> str:
    vault = ObsidianVault(settings.obsidian_vault_dir)
    vault.ensure_structure()
    return str(vault.write_note(folder, title, body, overwrite=overwrite))
