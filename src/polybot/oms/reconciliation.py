from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from polybot.live_execution.models import now_utc
from polybot.oms.order_manager import ManagedOrder
from polybot.wallet.models import OpenOrderState


@dataclass(frozen=True, slots=True)
class OMSReconciliationIssue:
    issue_type: str
    severity: str
    client_order_id: str | None = None
    exchange_order_id: str | None = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OMSReconciliationReport:
    generated_at: datetime
    checked_orders: int
    exchange_open_orders: int
    issues: list[OMSReconciliationIssue] = field(default_factory=list)

    @property
    def status(self) -> str:
        if any(issue.severity == "critical" for issue in self.issues):
            return "critical"
        if self.issues:
            return "warning"
        return "ok"

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "checked_orders": self.checked_orders,
            "exchange_open_orders": self.exchange_open_orders,
            "status": self.status,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def reconcile_orders(
    *,
    managed_orders: list[ManagedOrder],
    exchange_open_orders: list[OpenOrderState],
) -> OMSReconciliationReport:
    issues: list[OMSReconciliationIssue] = []
    exchange_by_id = {
        order.exchange_order_id: order
        for order in exchange_open_orders
        if order.exchange_order_id
    }
    for managed in managed_orders:
        if managed.exchange_order_id and managed.state.value in {"open", "partially_filled"}:
            if managed.exchange_order_id not in exchange_by_id:
                issues.append(
                    OMSReconciliationIssue(
                        issue_type="db_open_missing_on_exchange",
                        severity="critical",
                        client_order_id=managed.order.client_order_id,
                        exchange_order_id=managed.exchange_order_id,
                        description="OMS thinks order is open but exchange does not report it.",
                    )
                )
    managed_exchange_ids = {order.exchange_order_id for order in managed_orders if order.exchange_order_id}
    for exchange_order in exchange_open_orders:
        if exchange_order.exchange_order_id not in managed_exchange_ids:
            issues.append(
                OMSReconciliationIssue(
                    issue_type="exchange_open_missing_in_oms",
                    severity="warning",
                    client_order_id=exchange_order.client_order_id,
                    exchange_order_id=exchange_order.exchange_order_id,
                    description="Exchange reports open order unknown to OMS.",
                )
            )
    return OMSReconciliationReport(
        generated_at=now_utc(),
        checked_orders=len(managed_orders),
        exchange_open_orders=len(exchange_open_orders),
        issues=issues,
    )
