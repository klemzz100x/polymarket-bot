from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from polybot.live_execution.models import LiveOrder, RiskDecision, now_utc
from polybot.live_execution.safety import (
    DuplicateOrderProtector,
    EmergencyStop,
    LossCooldown,
    OrderRateLimiter,
)
from polybot.live_risk.live_constraints import LiveRiskConstraints
from polybot.live_risk.pre_trade_checks import PreTradeContext, run_pre_trade_checks


@dataclass(frozen=True, slots=True)
class RiskGateEvent:
    event_ts: datetime
    client_order_id: str
    allowed: bool
    reason: str
    checks: dict[str, bool] = field(default_factory=dict)


class LiveRiskGate:
    def __init__(
        self,
        *,
        constraints: LiveRiskConstraints | None = None,
        duplicate_protector: DuplicateOrderProtector | None = None,
        rate_limiter: OrderRateLimiter | None = None,
        loss_cooldown: LossCooldown | None = None,
        emergency_stop: EmergencyStop | None = None,
    ) -> None:
        self.constraints = constraints or LiveRiskConstraints()
        self.duplicate_protector = duplicate_protector or DuplicateOrderProtector()
        self.rate_limiter = rate_limiter or OrderRateLimiter()
        self.loss_cooldown = loss_cooldown or LossCooldown()
        self.emergency_stop = emergency_stop or EmergencyStop()
        self.events: list[RiskGateEvent] = []

    def evaluate(self, order: LiveOrder, context: PreTradeContext) -> RiskDecision:
        decision = run_pre_trade_checks(
            order=order,
            context=context,
            constraints=self.constraints,
        )
        extra_checks = {
            "emergency_stop_clear": not self.emergency_stop.triggered,
            "duplicate_order": not self.duplicate_protector.is_duplicate(order),
            "order_rate_limit": self.rate_limiter.allow(),
            "cooldown_after_loss_clear": not self.loss_cooldown.active(),
        }
        allowed = decision.allowed and all(extra_checks.values())
        checks = decision.checks | extra_checks
        failed = [name for name, passed in checks.items() if not passed]
        result = RiskDecision(
            allowed=allowed,
            reason="ok" if allowed else "ORDER_BLOCKED:" + ",".join(failed),
            severity="info" if allowed else "critical",
            checks=checks,
            metadata=decision.metadata,
        )
        if allowed:
            self.duplicate_protector.remember(order)
            self.rate_limiter.record()
        self.events.append(
            RiskGateEvent(
                event_ts=now_utc(),
                client_order_id=order.client_order_id,
                allowed=result.allowed,
                reason=result.reason,
                checks=result.checks,
            )
        )
        return result

    def record_loss(self, amount_usd: Decimal) -> None:
        if amount_usd > 0:
            self.loss_cooldown.record_loss()
