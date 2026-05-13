from decimal import Decimal

from polybot.live_execution.models import LiveFill
from polybot.oms.order_manager import ManagedOrder
from polybot.oms.order_state_machine import OMSOrderState, OrderStateMachine


class FillTracker:
    def __init__(self, state_machine: OrderStateMachine | None = None) -> None:
        self.state_machine = state_machine or OrderStateMachine()

    def apply_fill(self, managed: ManagedOrder, fill: LiveFill) -> ManagedOrder:
        previous_size = managed.filled_size
        new_size = managed.filled_size + fill.size
        if new_size <= 0:
            return managed
        if previous_size <= 0:
            managed.average_fill_price = fill.price
        elif managed.average_fill_price is not None:
            managed.average_fill_price = (
                (previous_size * managed.average_fill_price) + (fill.size * fill.price)
            ) / new_size
        managed.filled_size = new_size
        next_state = (
            OMSOrderState.FILLED
            if managed.filled_size >= managed.order.size
            else OMSOrderState.PARTIALLY_FILLED
        )
        transition = self.state_machine.transition(
            current=managed.state,
            next_state=next_state,
            reason="fill_received",
        )
        managed.state = transition.next_state
        managed.updated_at = transition.transitioned_at
        return managed

    def remaining_size(self, managed: ManagedOrder) -> Decimal:
        return max(managed.order.size - managed.filled_size, Decimal("0"))
