from datetime import UTC, datetime

from polybot.data.normalization import normalize_orderbook
from polybot.data.validation import validate_market_dataset


def test_validate_empty_orderbook_issue() -> None:
    snapshot = normalize_orderbook(
        {
            "market": "market-1",
            "asset_id": "asset-1",
            "timestamp": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
            "bids": [],
            "asks": [],
        }
    )

    report = validate_market_dataset(
        market_id="market-1",
        snapshots=[snapshot],
        trades=[],
        price_ticks=[],
    )

    assert report.status == "critical"
    assert any(issue.check_name == "empty_orderbook" for issue in report.issues)

