from datetime import datetime
from datetime import timedelta
from polybot.core.compat import UTC
from decimal import Decimal

from polybot.backtesting import BacktestConfig, BacktestEngine
from polybot.backtesting.results import SimulatedOrder
from polybot.backtesting.slippage_model import SlippageModel
from polybot.data.normalization import normalize_orderbook
from polybot.strategies.research import get_research_strategy


def test_slippage_partial_fill() -> None:
    snapshot = normalize_orderbook(
        {
            "market": "market-1",
            "asset_id": "asset-1",
            "timestamp": "2026-01-01T00:00:00Z",
            "bids": [{"price": "0.40", "size": "5"}],
            "asks": [{"price": "0.45", "size": "3"}],
        }
    )

    fill = SlippageModel().simulate_depth_fill(
        snapshot,
        side="buy",
        size=Decimal("10"),
        limit_price=Decimal("0.45"),
    )

    assert fill.filled_size == Decimal("3")
    assert fill.partial is True


def test_backtest_runs_on_mini_dataset() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    snapshots = [
        normalize_orderbook(
            {
                "market": "market-1",
                "asset_id": "asset-1",
                "timestamp": (base + timedelta(seconds=index)).isoformat(),
                "bids": [{"price": "0.40", "size": "100"}],
                "asks": [{"price": "0.55", "size": "100"}],
            }
        )
        for index in range(3)
    ]
    snapshots.append(
        normalize_orderbook(
            {
                "market": "market-1",
                "asset_id": "asset-1",
                "timestamp": (base + timedelta(seconds=4)).isoformat(),
                "bids": [{"price": "0.50", "size": "100"}],
                "asks": [{"price": "0.52", "size": "100"}],
            }
        )
    )

    config = BacktestConfig(
        strategy_name="wide-spread-mean-reversion",
        market_id="market-1",
        latency_ms=0,
        order_size=Decimal("10"),
    )
    result = BacktestEngine(config).run(
        strategy=get_research_strategy("wide-spread-mean-reversion"),
        snapshots=snapshots,
    )

    assert result.strategy_id == "wide-spread-mean-reversion"
    assert result.fill_rate >= Decimal("0")

