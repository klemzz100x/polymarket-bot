from datetime import UTC, datetime, timedelta

from polybot.data.ingestion.health import detect_stale_snapshots
from polybot.data.normalization import normalize_orderbook
from polybot.polymarket.websocket import build_market_subscription, parse_websocket_message


def test_stale_snapshot_detection() -> None:
    now = datetime(2026, 1, 1, 0, 1, tzinfo=UTC)
    snapshot = normalize_orderbook(
        {
            "market": "market-1",
            "asset_id": "asset-1",
            "timestamp": (now - timedelta(seconds=60)).isoformat(),
            "bids": [{"price": "0.40", "size": "10"}],
            "asks": [{"price": "0.60", "size": "10"}],
        }
    )

    stale = detect_stale_snapshots([snapshot], now=now, max_age_seconds=30)

    assert len(stale) == 1
    assert stale[0].asset_id == "asset-1"


def test_websocket_subscription_and_message_parser() -> None:
    subscription = build_market_subscription(["asset-1", "asset-2"])
    parsed = parse_websocket_message(b'{"event_type":"book","asset_id":"asset-1"}')

    assert subscription == {"assets_ids": ["asset-1", "asset-2"], "type": "market"}
    assert parsed == {"event_type": "book", "asset_id": "asset-1"}
    assert parse_websocket_message('[{"event_type":"trade"}]') == {
        "events": [{"event_type": "trade"}]
    }
    assert parse_websocket_message("PONG") is None
