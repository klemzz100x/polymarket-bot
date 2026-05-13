from datetime import datetime
from polybot.core.compat import UTC
from decimal import Decimal

from polybot.backtesting.results import BacktestTrade, SimulatedFill, SimulatedOrder
from polybot.paper_trading.equity import build_equity_snapshots
from polybot.paper_trading.models import PaperTradingResult


def test_build_equity_snapshots_from_paper_result() -> None:
    ts = datetime(2026, 1, 1, tzinfo=UTC)
    order = SimulatedOrder(
        order_id="order-1",
        market_id="market-1",
        asset_id="asset-1",
        side="buy",
        size=Decimal("10"),
        created_at=ts,
        limit_price=Decimal("0.50"),
    )
    fill = SimulatedFill(
        order_id="order-1",
        asset_id="asset-1",
        side="buy",
        requested_size=Decimal("10"),
        filled_size=Decimal("10"),
        average_price=Decimal("0.50"),
        fees=Decimal("0"),
        slippage=Decimal("0"),
        filled_at=ts,
        partial=False,
        latency_ms=0,
    )
    result = PaperTradingResult(
        run_id="run-1",
        market_id="market-1",
        strategy_name="strategy-1",
        started_at=ts,
        finished_at=ts,
        snapshot_count=1,
        signal_count=0,
        attempted_orders=1,
        filled_orders=1,
        rejected_orders=0,
        fills=[fill],
        trades=[BacktestTrade(order=order, fill=fill, gross_pnl=Decimal("1"), net_pnl=Decimal("1"))],
        signals=[],
        events=[],
        final_cash=Decimal("1001"),
        final_equity=Decimal("1001"),
        net_pnl=Decimal("1"),
        fees=Decimal("0"),
        max_exposure=Decimal("10"),
        fill_rate=Decimal("1"),
        partial_fill_rate=Decimal("0"),
    )

    snapshots = build_equity_snapshots(result)

    assert snapshots[0].equity == Decimal("1000")
    assert snapshots[-1].net_pnl == Decimal("1")
