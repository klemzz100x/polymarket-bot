from datetime import UTC, datetime
from decimal import Decimal
import asyncio

from polybot.exchange import PolymarketAdapter
from polybot.live_execution.modes import LiveExecutionMode, parse_live_execution_mode
from polybot.live_execution.models import ExecutionReport, LiveFill, LiveOrder
from polybot.live_execution.execution_quality import compute_live_execution_quality
from polybot.live_risk import LiveRiskConstraints, LiveRiskGate, PreTradeContext
from polybot.oms import OMSOrderState, OrderManager, reconcile_orders
from polybot.oms.fill_tracker import FillTracker
from polybot.risk.kill_switch import evaluate_kill_switch
from polybot.wallet.wallet_health import build_wallet_health


class _Settings:
    live_trading_enabled = False
    live_execution_mode = "SHADOW"
    require_manual_confirmation = True


def _order(order_id: str = "order-1") -> LiveOrder:
    return LiveOrder(
        client_order_id=order_id,
        market_id="market-1",
        asset_id="asset-1",
        side="buy",
        size=Decimal("1"),
        price=Decimal("0.50"),
        strategy_name="strategy-1",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        mode=LiveExecutionMode.MICRO_LIVE,
    )


def test_modes_default_to_disabled() -> None:
    assert parse_live_execution_mode(None) == LiveExecutionMode.DISABLED
    assert parse_live_execution_mode("bad-value") == LiveExecutionMode.DISABLED


def test_adapter_submit_disabled_by_default() -> None:
    asyncio.run(_adapter_submit_disabled_by_default())


async def _adapter_submit_disabled_by_default() -> None:
    adapter = PolymarketAdapter(settings=_Settings())
    order = adapter.prepare_order(
        client_order_id="client-1",
        market_id="market-1",
        asset_id="asset-1",
        side="buy",
        size=Decimal("1"),
        price=Decimal("0.50"),
        strategy_name="strategy-1",
    )
    report = await adapter.submit_order(order)

    assert report.accepted is False
    assert report.reason == "live_trading_disabled"


def test_risk_gate_blocks_and_duplicate_protects() -> None:
    gate = LiveRiskGate(
        constraints=LiveRiskConstraints(
            max_order_size_usd=Decimal("1"),
            require_manual_confirmation=True,
        )
    )
    order = _order()
    context = PreTradeContext(
        mode=LiveExecutionMode.MICRO_LIVE,
        live_trading_enabled=True,
        readiness_status="ready",
        kill_switch=evaluate_kill_switch(),
        manual_confirmation=True,
    )

    first = gate.evaluate(order, context)
    second = gate.evaluate(order, context)

    assert first.allowed is True
    assert second.allowed is False
    assert "duplicate_order" in second.reason


def test_oms_state_machine_fill_and_reconciliation() -> None:
    manager = OrderManager()
    managed = manager.prepare_order(_order())
    manager.apply_execution_report(
        ExecutionReport(
            client_order_id=managed.order.client_order_id,
            exchange_order_id="exchange-1",
            status="submitted",
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
            accepted=True,
        )
    )
    manager.mark_open(managed.order.client_order_id)
    FillTracker().apply_fill(
        managed,
        LiveFill(
            fill_id="fill-1",
            exchange_order_id="exchange-1",
            client_order_id=managed.order.client_order_id,
            market_id="market-1",
            asset_id="asset-1",
            side="buy",
            price=Decimal("0.50"),
            size=Decimal("1"),
            fee=Decimal("0"),
            filled_at=datetime(2026, 1, 1, tzinfo=UTC),
        ),
    )
    report = reconcile_orders(managed_orders=[managed], exchange_open_orders=[])

    assert managed.state == OMSOrderState.FILLED
    assert report.status == "ok"


def test_wallet_health_missing_wallet_is_critical() -> None:
    health = build_wallet_health(None, wallet_address="")

    assert health.status == "critical"
    assert "wallet_address_missing" in health.warnings


def test_live_execution_quality_uses_real_vs_theoretical_metrics() -> None:
    order = _order()
    fill = LiveFill(
        fill_id="fill-1",
        exchange_order_id="exchange-1",
        client_order_id=order.client_order_id,
        market_id=order.market_id,
        asset_id=order.asset_id,
        side=order.side,
        price=Decimal("0.51"),
        size=Decimal("1"),
        fee=Decimal("0"),
        filled_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC),
    )

    quality = compute_live_execution_quality(orders=[order], fills=[fill])

    assert quality.fill_ratio == Decimal("1")
    assert quality.average_slippage == Decimal("0.01")
