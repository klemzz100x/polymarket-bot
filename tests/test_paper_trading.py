from datetime import UTC, datetime
from decimal import Decimal

from polybot.data.normalization import normalize_orderbook
from polybot.obsidian.reports import render_paper_trading_report
from polybot.paper_trading import PaperTradingConfig, PaperTradingEngine


def test_paper_trading_signal_mode_generates_fill() -> None:
    snapshot = normalize_orderbook(
        {
            "market": "market-1",
            "asset_id": "asset-1",
            "timestamp": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
            "bids": [{"price": "0.50", "size": "100"}],
            "asks": [{"price": "0.52", "size": "10"}],
        }
    )

    result = PaperTradingEngine(
        PaperTradingConfig(
            market_id="market-1",
            decision_mode="signals",
            latency_ms=0,
            order_size=Decimal("5"),
        )
    ).run(snapshots=[snapshot], trades=[])

    assert result.signal_count >= 1
    assert result.filled_orders == 1
    assert result.fill_rate == Decimal("1")


def test_paper_trading_report_renders() -> None:
    snapshot = normalize_orderbook(
        {
            "market": "market-1",
            "asset_id": "asset-1",
            "timestamp": "2026-01-01T00:00:00Z",
            "bids": [{"price": "0.50", "size": "100"}],
            "asks": [{"price": "0.52", "size": "10"}],
        }
    )
    result = PaperTradingEngine(
        PaperTradingConfig(market_id="market-1", decision_mode="signals", latency_ms=0)
    ).run(snapshots=[snapshot], trades=[])

    note = render_paper_trading_report(result)

    assert "Paper Trading Report" in note
    assert "[[Backtesting]]" in note

