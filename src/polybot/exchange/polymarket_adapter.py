from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from polybot.exchange.execution_client import DisabledExecutionClient, ExecutionClient
from polybot.exchange.market_api import PolymarketMarketAPI
from polybot.exchange.order_api import PolymarketOrderAPI
from polybot.live_execution.models import ExecutionReport, LiveOrder, RiskDecision, now_utc
from polybot.live_execution.modes import (
    LiveExecutionMode,
    mode_allows_order_preparation,
    mode_allows_order_submission,
    parse_live_execution_mode,
)
from polybot.wallet.models import OpenOrderState, WalletBalance, WalletPosition

if TYPE_CHECKING:
    from polybot.core.config import Settings


class PolymarketAdapter:
    def __init__(
        self,
        *,
        settings: Settings,
        market_api: PolymarketMarketAPI | None = None,
        order_api: PolymarketOrderAPI | None = None,
        execution_client: ExecutionClient | None = None,
    ) -> None:
        self.settings = settings
        self.mode = parse_live_execution_mode(settings.live_execution_mode)
        self.market_api = market_api
        self.order_api = order_api or PolymarketOrderAPI(enabled=False)
        self.execution_client = execution_client or DisabledExecutionClient()

    async def get_market(self, market_id: str) -> dict[str, Any]:
        if self.market_api is None:
            return {}
        return await self.market_api.get_market(market_id)

    async def get_orderbook(self, token_id: str) -> dict[str, Any]:
        if self.market_api is None:
            return {}
        return await self.market_api.get_orderbook(token_id)

    async def get_positions(self, _wallet_address: str) -> list[WalletPosition]:
        return []

    async def get_balances(self, _wallet_address: str) -> list[WalletBalance]:
        return []

    async def get_open_orders(self, wallet_address: str) -> list[OpenOrderState]:
        return await self.order_api.get_open_orders(wallet_address)

    def prepare_order(
        self,
        *,
        client_order_id: str,
        market_id: str,
        asset_id: str,
        side: str,
        size: Decimal,
        price: Decimal,
        strategy_name: str,
        metadata: dict[str, Any] | None = None,
    ) -> LiveOrder:
        if not mode_allows_order_preparation(self.mode):
            raise PermissionError(f"mode_does_not_allow_order_preparation:{self.mode.value}")
        return LiveOrder(
            client_order_id=client_order_id,
            market_id=market_id,
            asset_id=asset_id,
            side=side,
            size=size,
            price=price,
            strategy_name=strategy_name,
            created_at=now_utc(),
            mode=self.mode,
            metadata=metadata or {},
        )

    def validate_order(self, order: LiveOrder) -> RiskDecision:
        checks = {
            "price_positive": order.price > 0,
            "price_below_one": order.price < 1,
            "size_positive": order.size > 0,
            "mode_prepares_orders": mode_allows_order_preparation(self.mode),
        }
        allowed = all(checks.values())
        return RiskDecision(
            allowed=allowed,
            reason="ok" if allowed else "exchange_order_validation_failed",
            severity="info" if allowed else "critical",
            checks=checks,
        )

    async def submit_order(self, order: LiveOrder) -> ExecutionReport:
        if not self.settings.live_trading_enabled:
            return _blocked(order, "live_trading_disabled")
        if self.mode != LiveExecutionMode.MICRO_LIVE:
            return _blocked(order, f"mode_blocks_submit:{self.mode.value}")
        if not mode_allows_order_submission(self.mode):
            return _blocked(order, "submission_not_allowed")
        if self.settings.require_manual_confirmation:
            return _blocked(order, "manual_confirmation_required")
        return await self.execution_client.submit_order(order)

    async def cancel_order(self, exchange_order_id: str) -> ExecutionReport:
        if not self.settings.live_trading_enabled or self.mode != LiveExecutionMode.MICRO_LIVE:
            return ExecutionReport(
                client_order_id="unknown",
                exchange_order_id=exchange_order_id,
                status="rejected",
                generated_at=now_utc(),
                accepted=False,
                reason="live_cancel_disabled",
            )
        return await self.execution_client.cancel_order(exchange_order_id)

    async def replace_order(self, exchange_order_id: str, replacement: LiveOrder) -> ExecutionReport:
        cancel_report = await self.cancel_order(exchange_order_id)
        if not cancel_report.accepted:
            return cancel_report
        return await self.submit_order(replacement)


def _blocked(order: LiveOrder, reason: str) -> ExecutionReport:
    return ExecutionReport(
        client_order_id=order.client_order_id,
        status="rejected",
        generated_at=now_utc(),
        accepted=False,
        reason=reason,
    )
