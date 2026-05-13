from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from polybot.backtesting import BacktestConfig, BacktestEngine, BacktestResult
from polybot.core.config import Settings, get_settings
from polybot.core.logging import get_logger
from polybot.core.security import verify_automation_secret
from polybot.data.normalization.time import normalize_datetime
from polybot.data.schemas import OrderBookSnapshot, Trade
from polybot.data.storage.database import create_session_factory
from polybot.data.storage.mappers import orderbook_snapshot_from_orm, trade_from_orm
from polybot.data.storage.repositories import OrderBookRepository, TradeRepository
from polybot.evaluation import (
    EvaluationReport,
    compare_backtest_vs_paper,
    compute_fill_quality,
    compute_signal_performance,
    compute_strategy_performance,
    detect_evaluation_anomalies,
)
from polybot.evaluation.models import now_utc
from polybot.evaluation.reporting import (
    render_backtest_vs_paper_report,
    render_daily_paper_trading_report,
    render_evaluation_report,
    render_fill_quality_report,
)
from polybot.knowledge.obsidian import ObsidianVault
from polybot.monitoring import record_backtest_result, record_paper_trading_result
from polybot.paper_trading import PaperTradingConfig, PaperTradingEngine, PaperTradingResult
from polybot.strategies.research import get_research_strategy

router = APIRouter(
    prefix="/evaluation",
    tags=["evaluation"],
    dependencies=[Depends(verify_automation_secret)],
)
logger = get_logger(__name__)


class EvaluationRunRequest(BaseModel):
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
    include_backtest: bool = True
    write_obsidian: bool = False


@router.post("/run")
async def run_evaluation(
    request: EvaluationRunRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    job_id, report, _paper, _backtest = await _build_report(request, settings)
    note = None
    if request.write_obsidian:
        note = _write_note(
            settings=settings,
            folder="Evaluation",
            title=f"Strategy Evaluation Report - {request.strategy} - {request.market_id}",
            body=render_evaluation_report(report),
        )
    logger.info("evaluation_run_completed", job_id=job_id, market_id=request.market_id)
    return {"job_id": job_id, "status": "completed", "report": report.to_dict(), "note": note}


@router.post("/daily-report")
async def daily_paper_trading_report(
    request: EvaluationRunRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    request = request.model_copy(update={"include_backtest": False})
    job_id, report, _paper, _backtest = await _build_report(request, settings)
    note = None
    if request.write_obsidian:
        note = _write_note(
            settings=settings,
            folder="Performance",
            title=f"Daily Paper Trading Report - {request.strategy} - {request.market_id}",
            body=render_daily_paper_trading_report(report),
        )
    logger.info("evaluation_daily_report_completed", job_id=job_id, market_id=request.market_id)
    return {"job_id": job_id, "status": "completed", "report": report.to_dict(), "note": note}


@router.post("/backtest-vs-paper")
async def backtest_vs_paper(
    request: EvaluationRunRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    request = request.model_copy(update={"include_backtest": True})
    job_id, report, _paper, _backtest = await _build_report(request, settings)
    note = None
    if request.write_obsidian:
        note = _write_note(
            settings=settings,
            folder="Evaluation",
            title=f"Backtest vs Paper Comparison - {request.strategy} - {request.market_id}",
            body=render_backtest_vs_paper_report(report),
        )
    logger.info("evaluation_backtest_vs_paper_completed", job_id=job_id, market_id=request.market_id)
    return {
        "job_id": job_id,
        "status": "completed",
        "comparison": report.comparison,
        "anomalies": [item.to_dict() for item in report.anomalies],
        "note": note,
    }


@router.post("/fill-quality")
async def fill_quality(
    request: EvaluationRunRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    request = request.model_copy(update={"include_backtest": False})
    job_id, report, _paper, _backtest = await _build_report(request, settings)
    note = None
    if request.write_obsidian and report.fill_quality:
        note = _write_note(
            settings=settings,
            folder="Evaluation",
            title=f"Fill Quality Report - {request.strategy} - {request.market_id}",
            body=render_fill_quality_report(report.fill_quality),
        )
    logger.info("evaluation_fill_quality_completed", job_id=job_id, market_id=request.market_id)
    return {
        "job_id": job_id,
        "status": "completed",
        "fill_quality": report.fill_quality.to_dict() if report.fill_quality else None,
        "anomalies": [item.to_dict() for item in report.anomalies],
        "note": note,
    }


async def _build_report(
    request: EvaluationRunRequest,
    settings: Settings,
) -> tuple[str, EvaluationReport, PaperTradingResult, BacktestResult | None]:
    job_id = str(uuid4())
    snapshots, trades = await _load_dataset(request, settings)
    strategy = None if request.decision_mode == "signals" else get_research_strategy(request.strategy)
    paper = PaperTradingEngine(
        PaperTradingConfig(
            market_id=request.market_id,
            strategy_name=request.strategy,
            run_id=job_id,
            initial_cash=Decimal(request.initial_cash),
            order_size=Decimal(request.order_size),
            fee_bps=Decimal(request.fee_bps),
            latency_ms=request.latency_ms,
            signal_window=request.signal_window,
            decision_mode=request.decision_mode,
        ),
        strategy=strategy,
    ).run(snapshots=snapshots, trades=trades)
    record_paper_trading_result(paper)

    backtest = None
    if request.include_backtest and request.decision_mode != "signals":
        backtest = BacktestEngine(
            BacktestConfig(
                strategy_name=request.strategy,
                market_id=request.market_id,
                initial_cash=Decimal(request.initial_cash),
                order_size=Decimal(request.order_size),
                fee_bps=Decimal(request.fee_bps),
                latency_ms=request.latency_ms,
            )
        ).run(strategy=get_research_strategy(request.strategy), snapshots=snapshots)
        record_backtest_result(backtest)

    paper_performance = compute_strategy_performance(paper, source="paper")
    backtest_performance = (
        compute_strategy_performance(backtest, source="backtest") if backtest else None
    )
    fill_quality = compute_fill_quality(paper)
    signal_performance = compute_signal_performance(paper)
    comparison = compare_backtest_vs_paper(backtest=backtest, paper=paper) if backtest else {}
    anomalies = detect_evaluation_anomalies(
        paper=paper_performance,
        backtest=backtest_performance,
        fill_quality=fill_quality,
        signal_quality=signal_performance,
    )
    period_start = min((snapshot.snapshot_ts for snapshot in snapshots), default=None)
    period_end = max((snapshot.snapshot_ts for snapshot in snapshots), default=None)
    report = EvaluationReport(
        report_id=job_id,
        market_id=request.market_id,
        strategy_name=request.strategy,
        generated_at=now_utc(),
        period_start=period_start,
        period_end=period_end,
        paper_performance=paper_performance,
        backtest_performance=backtest_performance,
        signal_performance=signal_performance,
        fill_quality=fill_quality,
        comparison=comparison,
        anomalies=anomalies,
        metadata={
            "decision_mode": request.decision_mode,
            "snapshot_count": len(snapshots),
            "trade_count": len(trades),
        },
    )
    return job_id, report, paper, backtest


async def _load_dataset(
    request: EvaluationRunRequest,
    settings: Settings,
) -> tuple[list[OrderBookSnapshot], list[Trade]]:
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
    return snapshots, trades


def _write_note(
    *,
    settings: Settings,
    folder: str,
    title: str,
    body: str,
) -> str:
    vault = ObsidianVault(settings.obsidian_vault_dir)
    vault.ensure_structure()
    return str(vault.write_note(folder, title, body, overwrite=True))
