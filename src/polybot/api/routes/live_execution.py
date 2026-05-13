from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from polybot.core.config import Settings, get_settings
from polybot.core.security import verify_automation_secret
from polybot.exchange import PolymarketAdapter
from polybot.live_execution.modes import parse_live_execution_mode
from polybot.live_risk import LiveRiskConstraints, LiveRiskGate, PreTradeContext
from polybot.risk.kill_switch import evaluate_kill_switch

router = APIRouter(
    prefix="/live-execution",
    tags=["live-execution"],
    dependencies=[Depends(verify_automation_secret)],
)


class PrepareLiveOrderRequest(BaseModel):
    market_id: str
    asset_id: str
    side: str = Field(pattern="^(buy|sell)$")
    size: str
    price: str
    strategy_name: str = "manual"
    readiness_status: str = "failed"
    stale_age_seconds: str = "0"
    latency_ms: str = "0"
    daily_loss_usd: str = "0"
    manual_confirmation: bool = False


@router.get("/status")
async def live_execution_status(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    mode = parse_live_execution_mode(settings.live_execution_mode)
    return {
        "live_trading_enabled": settings.live_trading_enabled,
        "live_execution_mode": mode.value,
        "kill_switch_enabled": settings.kill_switch_enabled,
        "require_manual_confirmation": settings.require_manual_confirmation,
        "max_order_size_usd": settings.max_order_size_usd,
        "max_daily_loss_usd": settings.max_daily_loss_usd,
        "max_open_positions": settings.max_open_positions,
        "default_safe_state": "DISABLED",
    }


@router.post("/prepare-order")
async def prepare_live_order(
    request: PrepareLiveOrderRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    adapter = PolymarketAdapter(settings=settings)
    mode = parse_live_execution_mode(settings.live_execution_mode)
    try:
        order = adapter.prepare_order(
            client_order_id=f"live-{uuid4()}",
            market_id=request.market_id,
            asset_id=request.asset_id,
            side=request.side,
            size=Decimal(request.size),
            price=Decimal(request.price),
            strategy_name=request.strategy_name,
            metadata={"source": "api_prepare_order", "no_auto_submit": True},
        )
    except PermissionError as exc:
        return {
            "status": "blocked",
            "reason": str(exc),
            "live_order_submitted": False,
        }

    constraints = LiveRiskConstraints(
        max_order_size_usd=Decimal(str(settings.max_order_size_usd)),
        max_daily_loss_usd=Decimal(str(settings.max_daily_loss_usd)),
        max_open_positions=settings.max_open_positions,
        require_manual_confirmation=settings.require_manual_confirmation,
    )
    kill_switch = evaluate_kill_switch() if settings.kill_switch_enabled else evaluate_kill_switch(api_healthy=False)
    decision = LiveRiskGate(constraints=constraints).evaluate(
        order,
        PreTradeContext(
            mode=mode,
            live_trading_enabled=settings.live_trading_enabled,
            readiness_status=request.readiness_status,
            kill_switch=kill_switch,
            daily_loss_usd=Decimal(request.daily_loss_usd),
            stale_age_seconds=Decimal(request.stale_age_seconds),
            latency_ms=Decimal(request.latency_ms),
            manual_confirmation=request.manual_confirmation,
        ),
    )
    return {
        "status": "prepared",
        "order": order.to_dict(),
        "risk_decision": decision.to_dict(),
        "live_order_submitted": False,
        "submit_note": "This endpoint never submits orders automatically.",
    }
