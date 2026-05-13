from polybot.live_execution.models import ExecutionReport, LiveOrder, now_utc
from polybot.wallet.models import OpenOrderState


class PolymarketOrderAPI:
    """Private order API shell. It is read-only until a real client is deliberately wired."""

    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled

    async def get_open_orders(self, _wallet_address: str) -> list[OpenOrderState]:
        return []

    async def submit_order(self, order: LiveOrder) -> ExecutionReport:
        if not self.enabled:
            return ExecutionReport(
                client_order_id=order.client_order_id,
                status="rejected",
                generated_at=now_utc(),
                accepted=False,
                reason="order_api_disabled",
            )
        return ExecutionReport(
            client_order_id=order.client_order_id,
            status="rejected",
            generated_at=now_utc(),
            accepted=False,
            reason="private_order_api_not_configured",
        )

    async def cancel_order(self, exchange_order_id: str) -> ExecutionReport:
        return ExecutionReport(
            client_order_id="unknown",
            exchange_order_id=exchange_order_id,
            status="rejected",
            generated_at=now_utc(),
            accepted=False,
            reason="cancel_api_disabled",
        )
