from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from polybot.live_execution.models import now_utc


class OMSOrderState(StrEnum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


TERMINAL_STATES = {
    OMSOrderState.FILLED,
    OMSOrderState.CANCELLED,
    OMSOrderState.REJECTED,
    OMSOrderState.EXPIRED,
}


ALLOWED_TRANSITIONS: dict[OMSOrderState, set[OMSOrderState]] = {
    OMSOrderState.PENDING: {OMSOrderState.SUBMITTED, OMSOrderState.REJECTED, OMSOrderState.EXPIRED},
    OMSOrderState.SUBMITTED: {OMSOrderState.OPEN, OMSOrderState.REJECTED, OMSOrderState.CANCELLED},
    OMSOrderState.OPEN: {
        OMSOrderState.PARTIALLY_FILLED,
        OMSOrderState.FILLED,
        OMSOrderState.CANCELLED,
        OMSOrderState.EXPIRED,
    },
    OMSOrderState.PARTIALLY_FILLED: {
        OMSOrderState.FILLED,
        OMSOrderState.CANCELLED,
        OMSOrderState.EXPIRED,
    },
    OMSOrderState.FILLED: set(),
    OMSOrderState.CANCELLED: set(),
    OMSOrderState.REJECTED: set(),
    OMSOrderState.EXPIRED: set(),
}


@dataclass(frozen=True, slots=True)
class StateTransition:
    previous_state: OMSOrderState
    next_state: OMSOrderState
    transitioned_at: datetime
    reason: str = ""


class OrderStateMachine:
    def can_transition(self, current: OMSOrderState, next_state: OMSOrderState) -> bool:
        return next_state in ALLOWED_TRANSITIONS[current]

    def transition(
        self,
        *,
        current: OMSOrderState,
        next_state: OMSOrderState,
        reason: str = "",
    ) -> StateTransition:
        if not self.can_transition(current, next_state):
            raise ValueError(f"invalid_oms_transition:{current.value}->{next_state.value}")
        return StateTransition(
            previous_state=current,
            next_state=next_state,
            transitioned_at=now_utc(),
            reason=reason,
        )
