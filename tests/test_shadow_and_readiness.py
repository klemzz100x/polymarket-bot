from datetime import datetime
from datetime import timedelta
from polybot.core.compat import UTC
from decimal import Decimal

from polybot.data.normalization import normalize_orderbook
from polybot.live_readiness import execution_quality_checks, score_from_checks
from polybot.risk.kill_switch import KillSwitchState, evaluate_kill_switch
from polybot.shadow_trading.models import ShadowOrder
from polybot.shadow_trading.order_simulator import simulate_shadow_fill
from polybot.shadow_trading.reporting import render_shadow_trading_report
from polybot.shadow_trading import ShadowTradingEngine
from polybot.paper_trading import PaperTradingConfig


def test_shadow_fill_respects_depth_and_partial_fill() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    snapshots = [
        normalize_orderbook(
            {
                "market": "market-1",
                "asset_id": "asset-1",
                "timestamp": (base + timedelta(milliseconds=500)).isoformat(),
                "bids": [{"price": "0.49", "size": "10"}],
                "asks": [{"price": "0.51", "size": "3"}],
            }
        )
    ]
    order = ShadowOrder(
        order_id="order-1",
        market_id="market-1",
        asset_id="asset-1",
        side="buy",
        size=Decimal("5"),
        created_at=base,
        limit_price=Decimal("0.51"),
    )

    fill = simulate_shadow_fill(order, snapshots, latency_ms=500)

    assert fill.fill_possible is True
    assert fill.partial is True
    assert fill.filled_size == Decimal("3")
    assert fill.fill_probability == Decimal("0.6")


def test_shadow_engine_and_report_stay_shadow_only() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    snapshots = [
        normalize_orderbook(
            {
                "market": "market-1",
                "asset_id": "asset-1",
                "timestamp": (base + timedelta(seconds=index)).isoformat(),
                "bids": [{"price": "0.50", "size": "100"}],
                "asks": [{"price": "0.52", "size": "10"}],
            }
        )
        for index in range(3)
    ]

    result = ShadowTradingEngine(
        PaperTradingConfig(
            market_id="market-1",
            strategy_name="wide-spread-mean-reversion",
            decision_mode="signals",
            latency_ms=0,
            order_size=Decimal("5"),
        )
    ).run(snapshots=snapshots, trades=[])
    rendered = render_shadow_trading_report(result)

    assert result.snapshot_count == 3
    assert result.decision_count >= 1
    assert "Shadow Trading Daily Report" in rendered
    assert "[[Risk Management]]" in rendered


def test_live_readiness_fails_on_missing_shadow_data() -> None:
    checks = execution_quality_checks(None)
    report = score_from_checks(
        report_id="report-1",
        checks=checks,
        kill_switch_state=KillSwitchState.ARMED.value,
    )

    assert report.status == "failed"
    assert report.live_readiness_score == Decimal("0")


def test_kill_switch_triggers_on_stale_data_and_slippage() -> None:
    evaluation = evaluate_kill_switch(
        stale_data_count=1,
        average_slippage=Decimal("0.10"),
    )

    assert evaluation.state == KillSwitchState.TRIGGERED
    assert {event.trigger.value for event in evaluation.events} >= {
        "stale_data",
        "excessive_slippage",
    }
