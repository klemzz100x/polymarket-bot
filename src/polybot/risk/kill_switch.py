from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from polybot.core.compat import UTC, StrEnum


class KillSwitchState(StrEnum):
    ARMED = "armed"
    TRIGGERED = "triggered"
    DISABLED = "disabled"


class KillSwitchTrigger(StrEnum):
    DRAWDOWN_EXCESSIVE = "drawdown_excessive"
    PNL_ANOMALY = "pnl_anomaly"
    STALE_DATA = "stale_data"
    API_FAILURE = "api_failure"
    DB_ISSUE = "db_issue"
    REDIS_ISSUE = "redis_issue"
    EXCESSIVE_SLIPPAGE = "excessive_slippage"
    EXCESSIVE_REJECTED_ORDERS = "excessive_rejected_orders"
    COLLECTOR_CRASH = "collector_crash"
    LATENCY_SPIKE = "latency_spike"
    MISSING_MARKET_DATA = "missing_market_data"


@dataclass(frozen=True, slots=True)
class KillSwitchEvent:
    state: KillSwitchState
    trigger: KillSwitchTrigger
    severity: str
    reason: str
    event_ts: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class KillSwitchEvaluation:
    state: KillSwitchState
    events: list[KillSwitchEvent]

    @property
    def triggered(self) -> bool:
        return self.state == KillSwitchState.TRIGGERED

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self) | {"triggered": self.triggered})


def evaluate_kill_switch(
    *,
    drawdown: Decimal = Decimal("0"),
    stale_data_count: int = 0,
    api_healthy: bool = True,
    db_healthy: bool = True,
    redis_healthy: bool = True,
    average_slippage: Decimal = Decimal("0"),
    rejected_order_rate: Decimal = Decimal("0"),
    collector_failures: int = 0,
    latency_ms: Decimal = Decimal("0"),
    missing_market_data: bool = False,
    drawdown_limit: Decimal = Decimal("0.20"),
    slippage_limit: Decimal = Decimal("0.05"),
    rejection_limit: Decimal = Decimal("0.50"),
    latency_limit_ms: Decimal = Decimal("5000"),
) -> KillSwitchEvaluation:
    events: list[KillSwitchEvent] = []
    if drawdown > drawdown_limit:
        events.append(_event(KillSwitchTrigger.DRAWDOWN_EXCESSIVE, "critical", "Drawdown exceeds configured limit.", {"drawdown": drawdown}))
    if stale_data_count > 0:
        events.append(_event(KillSwitchTrigger.STALE_DATA, "critical", "Stale market data detected.", {"stale_data_count": stale_data_count}))
    if not api_healthy:
        events.append(_event(KillSwitchTrigger.API_FAILURE, "critical", "API health check failed."))
    if not db_healthy:
        events.append(_event(KillSwitchTrigger.DB_ISSUE, "critical", "Database health check failed."))
    if not redis_healthy:
        events.append(_event(KillSwitchTrigger.REDIS_ISSUE, "warning", "Redis health check failed."))
    if average_slippage > slippage_limit:
        events.append(_event(KillSwitchTrigger.EXCESSIVE_SLIPPAGE, "critical", "Average slippage exceeds configured limit.", {"average_slippage": average_slippage}))
    if rejected_order_rate > rejection_limit:
        events.append(_event(KillSwitchTrigger.EXCESSIVE_REJECTED_ORDERS, "warning", "Rejected order rate exceeds configured limit.", {"rejected_order_rate": rejected_order_rate}))
    if collector_failures > 0:
        events.append(_event(KillSwitchTrigger.COLLECTOR_CRASH, "warning", "Collector failures detected.", {"collector_failures": collector_failures}))
    if latency_ms > latency_limit_ms:
        events.append(_event(KillSwitchTrigger.LATENCY_SPIKE, "critical", "Latency exceeds configured limit.", {"latency_ms": latency_ms}))
    if missing_market_data:
        events.append(_event(KillSwitchTrigger.MISSING_MARKET_DATA, "critical", "Required market data is missing."))
    return KillSwitchEvaluation(
        state=KillSwitchState.TRIGGERED if any(item.severity == "critical" for item in events) else KillSwitchState.ARMED,
        events=events,
    )


def _event(
    trigger: KillSwitchTrigger,
    severity: str,
    reason: str,
    metadata: dict[str, Any] | None = None,
) -> KillSwitchEvent:
    return KillSwitchEvent(
        state=KillSwitchState.TRIGGERED,
        trigger=trigger,
        severity=severity,
        reason=reason,
        metadata=metadata or {},
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum) and isinstance(value, str):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
