import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from polybot.live_execution.models import ExecutionReport, LiveFill
from polybot.oms.order_manager import ManagedOrder
from polybot.oms.reconciliation import OMSReconciliationReport


class OMSRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_order(self, managed: ManagedOrder) -> None:
        await self.session.execute(
            text(
                """
                INSERT INTO app.live_orders (
                    client_order_id, exchange_order_id, market_id, asset_id, strategy_name,
                    side, price, size, notional_usd, mode, state, rejection_reason, order_json
                )
                VALUES (
                    :client_order_id, :exchange_order_id, :market_id, :asset_id, :strategy_name,
                    :side, :price, :size, :notional_usd, :mode, :state, :rejection_reason,
                    CAST(:order_json AS JSONB)
                )
                ON CONFLICT (client_order_id) DO UPDATE SET
                    exchange_order_id = EXCLUDED.exchange_order_id,
                    state = EXCLUDED.state,
                    rejection_reason = EXCLUDED.rejection_reason,
                    order_json = EXCLUDED.order_json,
                    updated_at = now()
                """
            ),
            {
                "client_order_id": managed.order.client_order_id,
                "exchange_order_id": managed.exchange_order_id,
                "market_id": managed.order.market_id,
                "asset_id": managed.order.asset_id,
                "strategy_name": managed.order.strategy_name,
                "side": managed.order.side,
                "price": managed.order.price,
                "size": managed.order.size,
                "notional_usd": managed.order.notional_usd,
                "mode": managed.order.mode.value,
                "state": managed.state.value,
                "rejection_reason": managed.rejection_reason,
                "order_json": json.dumps(managed.order.to_dict(), default=str),
            },
        )

    async def insert_execution_report(self, report: ExecutionReport) -> None:
        await self.session.execute(
            text(
                """
                INSERT INTO app.live_execution_reports (
                    client_order_id, exchange_order_id, status, accepted, reason, report
                )
                VALUES (
                    :client_order_id, :exchange_order_id, :status, :accepted, :reason,
                    CAST(:report AS JSONB)
                )
                """
            ),
            {
                "client_order_id": report.client_order_id,
                "exchange_order_id": report.exchange_order_id,
                "status": report.status,
                "accepted": report.accepted,
                "reason": report.reason,
                "report": json.dumps(report.to_dict(), default=str),
            },
        )

    async def insert_fill(self, fill: LiveFill) -> None:
        await self.session.execute(
            text(
                """
                INSERT INTO app.live_fills (
                    fill_id, exchange_order_id, client_order_id, market_id,
                    asset_id, side, price, size, fee, filled_at, raw_payload
                )
                VALUES (
                    :fill_id, :exchange_order_id, :client_order_id, :market_id,
                    :asset_id, :side, :price, :size, :fee, :filled_at,
                    CAST(:raw_payload AS JSONB)
                )
                ON CONFLICT (fill_id) DO NOTHING
                """
            ),
            {
                "fill_id": fill.fill_id,
                "exchange_order_id": fill.exchange_order_id,
                "client_order_id": fill.client_order_id,
                "market_id": fill.market_id,
                "asset_id": fill.asset_id,
                "side": fill.side,
                "price": fill.price,
                "size": fill.size,
                "fee": fill.fee,
                "filled_at": fill.filled_at,
                "raw_payload": json.dumps(fill.raw_payload, default=str),
            },
        )

    async def insert_reconciliation_report(self, report: OMSReconciliationReport) -> None:
        await self.session.execute(
            text(
                """
                INSERT INTO app.oms_reconciliation_reports (
                    generated_at, status, checked_orders, exchange_open_orders, report
                )
                VALUES (
                    :generated_at, :status, :checked_orders, :exchange_open_orders,
                    CAST(:report AS JSONB)
                )
                """
            ),
            {
                "generated_at": report.generated_at,
                "status": report.status,
                "checked_orders": report.checked_orders,
                "exchange_open_orders": report.exchange_open_orders,
                "report": json.dumps(report.to_dict(), default=str),
            },
        )
