from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text

from polybot.core.config import Settings, get_settings
from polybot.core.logging import get_logger
from polybot.core.security import verify_automation_secret
from polybot.data.normalization.time import normalize_datetime
from polybot.data.storage.database import create_session_factory
from polybot.data.storage.mappers import orderbook_snapshot_from_orm, trade_from_orm
from polybot.data.storage.repositories import OrderBookRepository, TradeRepository
from polybot.knowledge.obsidian import ObsidianVault
from polybot.live_readiness import (
    execution_quality_checks,
    infrastructure_checks,
    risk_checks,
    score_from_checks,
)
from polybot.live_readiness.kill_switch_checks import evaluate_pre_live_kill_switch
from polybot.live_readiness.readiness_checks import check_threshold
from polybot.live_readiness.readiness_score import ReadinessCheckResult
from polybot.live_readiness.reporting import render_live_readiness_report
from polybot.live_readiness.storage import LiveReadinessRepository
from polybot.monitoring import record_live_readiness_report, record_shadow_trading_result
from polybot.monitoring.telegram import send_telegram_message
from polybot.monitoring.telegram_templates import (
    kill_switch_triggered,
    readiness_degraded,
)
from polybot.paper_trading import PaperTradingConfig
from polybot.risk.kill_switch import evaluate_kill_switch
from polybot.shadow_trading import ShadowTradingEngine, ShadowTradingResult
from polybot.shadow_trading.reporting import render_shadow_trading_report
from polybot.shadow_trading.storage import ShadowTradingRepository

router = APIRouter(tags=["pre-live"], dependencies=[Depends(verify_automation_secret)])
logger = get_logger(__name__)


class ShadowTradingRunRequest(BaseModel):
    market_id: str
    strategy: str = "wide-spread-mean-reversion"
    start: str | None = None
    end: str | None = None
    limit: int = Field(default=5000, ge=1, le=50000)
    initial_cash: str = "1000"
    order_size: str = "10"
    max_position: str = "100"
    max_market_exposure: str = "250"
    fee_bps: str = "0"
    latency_ms: int = Field(default=500, ge=0, le=60000)
    signal_window: int = Field(default=20, ge=2, le=500)
    persist_db: bool = True
    write_obsidian: bool = False


class LiveReadinessRunRequest(BaseModel):
    market_id: str | None = None
    strategy: str = "wide-spread-mean-reversion"
    start: str | None = None
    end: str | None = None
    limit: int = Field(default=5000, ge=1, le=50000)
    initial_cash: str = "1000"
    order_size: str = "10"
    max_position: str = "100"
    max_market_exposure: str = "250"
    fee_bps: str = "0"
    latency_ms: int = Field(default=500, ge=0, le=60000)
    signal_window: int = Field(default=20, ge=2, le=500)
    drawdown: str = "0"
    exposure: str = "0"
    stale_data_count: int | None = None
    collector_failures: int = Field(default=0, ge=0)
    missing_market_data: bool = False
    db_healthy: bool | None = None
    redis_healthy: bool | None = None
    api_healthy: bool = True
    collectors_healthy: bool = True
    websocket_healthy: bool = True
    telegram_ready: bool | None = None
    dashboard_ready: bool = True
    obsidian_ready: bool | None = None
    persist_db: bool = True
    write_obsidian: bool = False
    send_telegram_alerts: bool = False


@router.post("/shadow-trading/run")
async def run_shadow_trading(
    request: ShadowTradingRunRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    result = await _run_shadow(request, settings)
    record_shadow_trading_result(result)
    note = None
    if request.write_obsidian:
        note = _write_note(
            settings=settings,
            folder="Shadow-Trading",
            title=f"Shadow Trading Daily Report - {request.strategy} - {request.market_id}",
            body=render_shadow_trading_report(result),
        )
    if request.persist_db:
        session_factory = create_session_factory(settings.database_url)
        async with session_factory() as session:
            await ShadowTradingRepository(session).insert_result(result)
            await session.commit()
    logger.info("shadow_trading_run_completed", run_id=result.run_id, market_id=request.market_id)
    return {"job_id": result.run_id, "status": "completed", "result": result.to_dict(), "note": note}


@router.get("/shadow-trading/latest")
async def latest_shadow_trading(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    session_factory = create_session_factory(settings.database_url)
    async with session_factory() as session:
        latest = await ShadowTradingRepository(session).latest_result()
    return {"status": "ok", "latest": _json_ready(latest)}


@router.post("/live-readiness/run")
async def run_live_readiness(
    request: LiveReadinessRunRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    report_id = str(uuid4())
    shadow = await _run_shadow(_shadow_request_from_readiness(request), settings) if request.market_id else None
    if shadow is not None:
        record_shadow_trading_result(shadow)

    session_factory = create_session_factory(settings.database_url)
    async with session_factory() as session:
        db_healthy = (
            request.db_healthy
            if request.db_healthy is not None
            else bool((await session.execute(text("SELECT 1 AS ok"))).scalar_one_or_none())
        )
        latest_shadow = await ShadowTradingRepository(session).latest_result() if shadow is None else None
        stale_data_count = (
            request.stale_data_count
            if request.stale_data_count is not None
            else await _stale_data_count(session)
        )

        rejected_rate = _shadow_rejected_rate(shadow, latest_shadow)
        checks = [
            *(_execution_checks_from_latest(latest_shadow) if shadow is None else execution_quality_checks(shadow)),
            *risk_checks(
                drawdown=Decimal(request.drawdown),
                exposure=Decimal(request.exposure),
                rejected_rate=rejected_rate,
            ),
            *infrastructure_checks(
                db_healthy=db_healthy,
                redis_healthy=(
                    request.redis_healthy
                    if request.redis_healthy is not None
                    else await _redis_healthy(settings.redis_url)
                ),
                api_healthy=request.api_healthy,
                collectors_healthy=request.collectors_healthy,
                websocket_healthy=request.websocket_healthy,
                telegram_ready=(
                    request.telegram_ready
                    if request.telegram_ready is not None
                    else _telegram_ready(settings)
                ),
                dashboard_ready=request.dashboard_ready,
                obsidian_ready=(
                    request.obsidian_ready
                    if request.obsidian_ready is not None
                    else Path(settings.obsidian_vault_dir).exists()
                ),
                stale_data_count=stale_data_count,
            ),
        ]

        kill_switch = (
            evaluate_pre_live_kill_switch(
                shadow=shadow,
                drawdown=Decimal(request.drawdown),
                stale_data_count=stale_data_count,
                db_healthy=db_healthy,
                redis_healthy=checks_by_name(checks).get("redis_healthy", True),
                api_healthy=request.api_healthy,
                collector_failures=request.collector_failures,
                rejected_order_rate=rejected_rate,
                missing_market_data=request.missing_market_data,
            )
            if shadow is not None
            else evaluate_kill_switch(
                drawdown=Decimal(request.drawdown),
                stale_data_count=stale_data_count,
                api_healthy=request.api_healthy,
                db_healthy=db_healthy,
                redis_healthy=checks_by_name(checks).get("redis_healthy", True),
                average_slippage=Decimal(str((latest_shadow or {}).get("average_slippage") or "0")),
                rejected_order_rate=rejected_rate,
                collector_failures=request.collector_failures,
                latency_ms=Decimal(str((latest_shadow or {}).get("average_delay_ms") or "0")),
                missing_market_data=request.missing_market_data,
            )
        )
        report = score_from_checks(
            report_id=report_id,
            checks=checks,
            kill_switch_state=kill_switch.state.value,
            metadata={
                "market_id": request.market_id,
                "strategy": request.strategy,
                "shadow_run_id": shadow.run_id if shadow else (latest_shadow or {}).get("id"),
                "no_live_trading": True,
            },
        )
        record_live_readiness_report(report)

        if request.persist_db:
            if shadow is not None:
                await ShadowTradingRepository(session).insert_result(shadow)
            repo = LiveReadinessRepository(session)
            await repo.insert_report(report)
            await repo.insert_kill_switch_events(kill_switch.events)
            await session.commit()

    note = None
    if request.write_obsidian:
        note = _write_note(
            settings=settings,
            folder="Live-Readiness",
            title=f"Live Readiness Report - {report.status}",
            body=render_live_readiness_report(report),
        )
    if request.send_telegram_alerts and (report.status != "ready" or kill_switch.triggered):
        send_telegram_message(settings=settings, text=readiness_degraded(report))
        for event in kill_switch.events:
            send_telegram_message(settings=settings, text=kill_switch_triggered(event))

    logger.info("live_readiness_completed", report_id=report_id, status=report.status)
    return {
        "job_id": report_id,
        "status": "completed",
        "report": report.to_dict(),
        "kill_switch": kill_switch.to_dict(),
        "shadow_result": shadow.to_dict() if shadow else None,
        "note": note,
    }


@router.get("/live-readiness/latest")
async def latest_live_readiness(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    session_factory = create_session_factory(settings.database_url)
    async with session_factory() as session:
        latest = await LiveReadinessRepository(session).latest_report()
    return {"status": "ok", "latest": _json_ready(latest)}


async def _run_shadow(
    request: ShadowTradingRunRequest,
    settings: Settings,
) -> ShadowTradingResult:
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
    return ShadowTradingEngine(
        PaperTradingConfig(
            market_id=request.market_id,
            strategy_name=request.strategy,
            run_id=str(uuid4()),
            initial_cash=Decimal(request.initial_cash),
            order_size=Decimal(request.order_size),
            max_position=Decimal(request.max_position),
            max_market_exposure=Decimal(request.max_market_exposure),
            fee_bps=Decimal(request.fee_bps),
            latency_ms=request.latency_ms,
            signal_window=request.signal_window,
            decision_mode="signals",
            ledger_path=None,
        )
    ).run(snapshots=snapshots, trades=trades)


def _shadow_request_from_readiness(request: LiveReadinessRunRequest) -> ShadowTradingRunRequest:
    if request.market_id is None:
        raise ValueError("market_id is required to run shadow trading")
    return ShadowTradingRunRequest(
        market_id=request.market_id,
        strategy=request.strategy,
        start=request.start,
        end=request.end,
        limit=request.limit,
        initial_cash=request.initial_cash,
        order_size=request.order_size,
        max_position=request.max_position,
        max_market_exposure=request.max_market_exposure,
        fee_bps=request.fee_bps,
        latency_ms=request.latency_ms,
        signal_window=request.signal_window,
        persist_db=False,
        write_obsidian=False,
    )


def _execution_checks_from_latest(latest: dict | None) -> list[ReadinessCheckResult]:
    if latest is None:
        return execution_quality_checks(None)
    snapshot_count = int(latest.get("snapshot_count") or 0)
    decision_count = int(latest.get("decision_count") or 0)
    return [
        ReadinessCheckResult(
            name="shadow_market_data_available",
            passed=snapshot_count > 0,
            score=Decimal("100") if snapshot_count > 0 else Decimal("0"),
            severity="critical",
            message="ok" if snapshot_count > 0 else "No orderbook snapshots were available.",
            metadata={"snapshot_count": snapshot_count},
        ),
        ReadinessCheckResult(
            name="shadow_decision_flow_active",
            passed=decision_count > 0,
            score=Decimal("100") if decision_count > 0 else Decimal("50"),
            severity="warning",
            message="ok" if decision_count > 0 else "No shadow decisions were generated.",
            metadata={"decision_count": decision_count},
        ),
        check_threshold(
            "execution_shadow_slippage",
            Decimal(str(latest.get("average_slippage") or "0")),
            maximum=Decimal("0.05"),
            message="Shadow slippage is too high.",
        ),
        check_threshold(
            "execution_shadow_latency",
            Decimal(str(latest.get("average_delay_ms") or "0")),
            maximum=Decimal("5000"),
            message="Shadow execution delay is too high.",
        ),
        ReadinessCheckResult(
            name="shadow_fill_realism",
            passed=int(latest.get("impossible_fill_count") or 0) == 0,
            score=Decimal("100") if int(latest.get("impossible_fill_count") or 0) == 0 else Decimal("0"),
            severity="critical",
            message="ok"
            if int(latest.get("impossible_fill_count") or 0) == 0
            else "Impossible fills detected in latest shadow run.",
            metadata={"impossible_fill_count": int(latest.get("impossible_fill_count") or 0)},
        ),
    ]


def _shadow_rejected_rate(shadow: ShadowTradingResult | None, latest: dict | None) -> Decimal:
    if shadow is not None:
        if shadow.decision_count == 0:
            return Decimal("0")
        rejected = sum(1 for decision in shadow.decisions if decision.status == "risk_rejected")
        return Decimal(rejected) / Decimal(shadow.decision_count)
    if latest is None:
        return Decimal("0")
    result = latest.get("result") or {}
    if not isinstance(result, dict):
        return Decimal("0")
    decisions = result.get("decisions") or []
    if not decisions:
        return Decimal("0")
    rejected = sum(1 for item in decisions if item.get("status") == "risk_rejected")
    return Decimal(rejected) / Decimal(len(decisions))


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


async def _redis_healthy(redis_url: str) -> bool:
    try:
        from redis.asyncio import Redis
    except ImportError:  # pragma: no cover
        return False
    client = Redis.from_url(redis_url)
    try:
        return bool(await client.ping())
    except Exception:
        return False
    finally:
        await client.aclose()


def _telegram_ready(settings: Settings) -> bool:
    return bool(
        settings.telegram_enabled
        and settings.telegram_notifications
        and settings.telegram_bot_token
        and settings.telegram_chat_id
    )


def checks_by_name(checks: list[ReadinessCheckResult]) -> dict[str, bool]:
    return {check.name: check.passed for check in checks}


def _write_note(*, settings: Settings, folder: str, title: str, body: str) -> str:
    vault = ObsidianVault(settings.obsidian_vault_dir)
    vault.ensure_structure()
    return str(vault.write_note(folder, title, body, overwrite=True))


def _json_ready(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
