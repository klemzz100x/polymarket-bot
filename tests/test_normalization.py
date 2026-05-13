from decimal import Decimal

from polybot.data.normalization import normalize_market, normalize_orderbook, normalize_public_trade
from polybot.data.normalization.time import normalize_unix_timestamp


def test_normalize_unix_timestamp_seconds_and_millis() -> None:
    seconds = normalize_unix_timestamp(1700000000)
    millis = normalize_unix_timestamp(1700000000000)

    assert seconds == millis


def test_normalize_market_extracts_outcomes() -> None:
    market = normalize_market(
        {
            "id": "1",
            "question": "Will X happen?",
            "conditionId": "0x" + "1" * 64,
            "outcomes": '["Yes", "No"]',
            "outcomePrices": '["0.4", "0.6"]',
            "clobTokenIds": '["101", "202"]',
            "active": True,
            "closed": False,
        }
    )

    assert market.outcomes[0].asset_id == "101"
    assert market.outcomes[0].price == Decimal("0.4")


def test_normalize_orderbook_calculates_spread() -> None:
    book = normalize_orderbook(
        {
            "market": "0x" + "1" * 64,
            "asset_id": "101",
            "timestamp": "1700000000000",
            "bids": [{"price": "0.40", "size": "10"}],
            "asks": [{"price": "0.45", "size": "8"}],
        }
    )

    assert book.spread == Decimal("0.05")


def test_normalize_trade_uses_transaction_hash() -> None:
    trade = normalize_public_trade(
        {
            "conditionId": "0x" + "1" * 64,
            "asset": "101",
            "price": 0.4,
            "size": 10,
            "timestamp": 1700000000,
            "transactionHash": "0xabc",
        }
    )

    assert trade.transaction_hash == "0xabc"

