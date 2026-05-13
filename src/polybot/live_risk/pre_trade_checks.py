from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from polybot.live_execution.modes import LiveExecutionMode, mode_allows_order_submission
from polybot.live_execution.models import LiveOrder, PositionExposure, RiskDecision
from polybot.live_risk.exposure_limits import exposure_checks
from polybot.live_risk.live_constraints import LiveRiskConstraints
from polybot.risk.kill_switch import KillSwitchEvaluation


@dataclass(frozen=True, slots=True)
class PreTradeContext:
    mode: LiveExecutionMode
    live_trading_enabled: bool
    readiness_status: str
    kill_switch: KillSwitchEvaluation
    current_exposures: list[PositionExposure] = field(default_factory=list)
    daily_loss_usd: Decimal = Decimal("0")
    stale_age_seconds: Decimal = Decimal("0")
    latency_ms: Decimal = Decimal("0")
    manual_confirmation: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


def run_pre_trade_checks(
    *,
    order: LiveOrder,
    context: PreTradeContext,
    constraints: LiveRiskConstraints,
) -> RiskDecision:
    checks = {
        "live_trading_enabled": context.live_trading_enabled,
        "mode_allows_submission": mode_allows_order_submission(context.mode),
        "readiness_ready": context.readiness_status == "ready",
        "kill_switch_armed": not context.kill_switch.triggered,
        "max_order_size": order.notional_usd <= constraints.max_order_size_usd,
        "max_daily_loss": context.daily_loss_usd <= constraints.max_daily_loss_usd,
        "stale_data_check": context.stale_age_seconds <= constraints.max_stale_age_seconds,
        "latency_check": context.latency_ms <= constraints.max_latency_ms,
        "manual_confirmation": (
            context.manual_confirmation if constraints.require_manual_confirmation else True
        ),
        **exposure_checks(
            current=context.current_exposures,
            order=order,
            constraints=constraints,
        ),
    }
    allowed = all(checks.values())
    failed = [name for name, passed in checks.items() if not passed]
    return RiskDecision(
        allowed=allowed,
        reason="ok" if allowed else "ORDER_BLOCKED:" + ",".join(failed),
        severity="info" if allowed else "critical",
        checks=checks,
        metadata={
            "order_notional_usd": str(order.notional_usd),
            "daily_loss_usd": str(context.daily_loss_usd),
            "stale_age_seconds": str(context.stale_age_seconds),
            "latency_ms": str(context.latency_ms),
        },
    )
