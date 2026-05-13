from polybot.data.normalization import normalize_orderbook
from polybot.research.inefficiencies import scan_inefficiencies


def test_scan_detects_wide_spread() -> None:
    snapshot = normalize_orderbook(
        {
            "market": "market-1",
            "asset_id": "asset-1",
            "timestamp": "2026-01-01T00:00:00Z",
            "bids": [{"price": "0.30", "size": "100"}],
            "asks": [{"price": "0.60", "size": "100"}],
        }
    )

    report = scan_inefficiencies(market_id="market-1", snapshots=[snapshot], trades=[])

    assert any(signal.signal_type == "wide_spread" for signal in report.signals)

