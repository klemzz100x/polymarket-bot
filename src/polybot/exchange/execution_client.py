from typing import Protocol

from polybot.live_execution.models import ExecutionReport, LiveOrder, now_utc


class ExecutionClient(Protocol):
    async def submit_order(self, order: LiveOrder) -> ExecutionReport:
        ...

    async def cancel_order(self, exchange_order_id: str) -> ExecutionReport:
        ...


class DisabledExecutionClient:
    async def submit_order(self, order: LiveOrder) -> ExecutionReport:
        return ExecutionReport(
            client_order_id=order.client_order_id,
            status="rejected",
            generated_at=now_utc(),
            accepted=False,
            reason="live_execution_client_disabled",
        )

    async def cancel_order(self, exchange_order_id: str) -> ExecutionReport:
        return ExecutionReport(
            client_order_id="unknown",
            exchange_order_id=exchange_order_id,
            status="rejected",
            generated_at=now_utc(),
            accepted=False,
            reason="live_execution_client_disabled",
        )
