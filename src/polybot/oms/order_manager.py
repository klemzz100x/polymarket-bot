from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from polybot.live_execution.models import ExecutionReport, LiveOrder, now_utc
from polybot.live_execution.safety import DuplicateOrderProtector
from polybot.oms.order_state_machine import OMSOrderState, OrderStateMachine


@dataclass(slots=True)
class ManagedOrder:
    order: LiveOrder
    state: OMSOrderState = OMSOrderState.PENDING
    exchange_order_id: str | None = None
    filled_size: Decimal = Decimal("0")
    average_fill_price: Decimal | None = None
    created_at: datetime = field(default_factory=now_utc)
    updated_at: datetime = field(default_factory=now_utc)
    rejection_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        data["order"] = self.order.to_dict()
        return data


class OrderManager:
    def __init__(
        self,
        *,
        state_machine: OrderStateMachine | None = None,
        duplicate_protector: DuplicateOrderProtector | None = None,
    ) -> None:
        self.state_machine = state_machine or OrderStateMachine()
        self.duplicate_protector = duplicate_protector or DuplicateOrderProtector()
        self.orders: dict[str, ManagedOrder] = {}

    def prepare_order(self, order: LiveOrder) -> ManagedOrder:
        if self.duplicate_protector.is_duplicate(order):
            managed = ManagedOrder(order=order, state=OMSOrderState.REJECTED)
            managed.rejection_reason = "duplicate_order"
            self.orders[order.client_order_id] = managed
            return managed
        self.duplicate_protector.remember(order)
        managed = ManagedOrder(order=order)
        self.orders[order.client_order_id] = managed
        return managed

    def apply_execution_report(self, report: ExecutionReport) -> ManagedOrder:
        managed = self.orders.get(report.client_order_id)
        if managed is None:
            raise KeyError(f"unknown_client_order_id:{report.client_order_id}")
        if report.accepted:
            self._transition(managed, OMSOrderState.SUBMITTED, reason=report.reason)
            managed.exchange_order_id = report.exchange_order_id
        else:
            self._transition(managed, OMSOrderState.REJECTED, reason=report.reason)
            managed.rejection_reason = report.reason
        return managed

    def mark_open(self, client_order_id: str) -> ManagedOrder:
        managed = self.orders[client_order_id]
        self._transition(managed, OMSOrderState.OPEN, reason="exchange_open")
        return managed

    def mark_cancelled(self, client_order_id: str, reason: str = "cancelled") -> ManagedOrder:
        managed = self.orders[client_order_id]
        self._transition(managed, OMSOrderState.CANCELLED, reason=reason)
        return managed

    def _transition(self, managed: ManagedOrder, state: OMSOrderState, *, reason: str) -> None:
        transition = self.state_machine.transition(
            current=managed.state,
            next_state=state,
            reason=reason,
        )
        managed.state = transition.next_state
        managed.updated_at = transition.transitioned_at
