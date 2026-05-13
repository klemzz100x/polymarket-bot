from decimal import Decimal

from polybot.data.normalization import normalize_orderbook
from polybot.research.metrics import compute_orderbook_metrics


def test_compute_orderbook_metrics() -> None:
    book = normalize_orderbook(
        {
            "market": "0x" + "1" * 64,
            "asset_id": "101",
            "timestamp": "1700000000",
            "bids": [{"price": "0.40", "size": "10"}],
            "asks": [{"price": "0.45", "size": "8"}],
        }
    )

    metrics = compute_orderbook_metrics(book)

    assert metrics.spread == Decimal("0.05")
    assert metrics.total_depth == Decimal("18")

