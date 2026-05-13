from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any

from polybot.data.normalization.time import normalize_datetime, normalize_unix_timestamp, utc_now
from polybot.data.schemas import Market, MarketMetadata, OrderBookLevel, OrderBookSnapshot, Outcome
from polybot.data.schemas.orderbook import OrderBookSide
from polybot.data.schemas.trade import PriceTick, Trade


def normalize_market(raw: dict[str, Any]) -> Market:
    market_id = _string(raw.get("id")) or _string(raw.get("conditionId")) or _string(raw.get("slug"))
    if market_id is None:
        raise ValueError("Market payload missing id/conditionId/slug")

    condition_id = _string(raw.get("conditionId") or raw.get("condition_id"))
    outcomes = _parse_jsonish(raw.get("outcomes"))
    prices = _parse_jsonish(raw.get("outcomePrices"))
    token_ids = _parse_jsonish(raw.get("clobTokenIds") or raw.get("clob_token_ids"))
    normalized_outcomes = [
        Outcome(
            market_id=market_id,
            condition_id=condition_id,
            outcome_index=index,
            name=str(name),
            asset_id=_safe_list_get(token_ids, index),
            price=_decimal_or_none(_safe_list_get(prices, index)),
            raw_payload={"name": name},
        )
        for index, name in enumerate(outcomes)
    ]

    metadata = MarketMetadata(
        market_id=market_id,
        condition_id=condition_id,
        slug=_string(raw.get("slug")),
        category=_string(raw.get("category")),
        tags=_extract_tags(raw),
        event_slug=_extract_event_slug(raw),
        start_date=normalize_datetime(raw.get("startDate") or raw.get("startDateIso")),
        end_date=normalize_datetime(raw.get("endDate") or raw.get("endDateIso")),
        game_start_time=normalize_datetime(raw.get("gameStartTime")),
        description=_string(raw.get("description")),
        raw_payload=raw,
    )

    return Market(
        market_id=market_id,
        condition_id=condition_id,
        question=_string(raw.get("question")) or _string(raw.get("title")) or market_id,
        slug=_string(raw.get("slug")),
        active=bool(raw.get("active", False)),
        closed=bool(raw.get("closed", False)),
        archived=bool(raw.get("archived", False)),
        accepting_orders=_bool_or_none(raw.get("acceptingOrders")),
        enable_order_book=_bool_or_none(raw.get("enableOrderBook")),
        category=_string(raw.get("category")),
        volume=_decimal_or_none(raw.get("volumeNum") or raw.get("volume")),
        liquidity=_decimal_or_none(raw.get("liquidityNum") or raw.get("liquidity")),
        start_date=metadata.start_date,
        end_date=metadata.end_date,
        created_at=normalize_datetime(raw.get("createdAt")),
        updated_at=normalize_datetime(raw.get("updatedAt")),
        outcomes=normalized_outcomes,
        metadata=metadata,
        raw_payload=raw,
    )


def normalize_orderbook(raw: dict[str, Any], received_at: datetime | None = None) -> OrderBookSnapshot:
    received = received_at or utc_now()
    condition_id = _string(raw.get("market"))
    asset_id = _string(raw.get("asset_id") or raw.get("token_id"))
    if condition_id is None or asset_id is None:
        raise ValueError("Orderbook payload missing market or asset_id")

    return OrderBookSnapshot(
        condition_id=condition_id,
        asset_id=asset_id,
        snapshot_ts=normalize_datetime(raw.get("timestamp")) or received,
        received_at=received,
        book_hash=_string(raw.get("hash")),
        min_order_size=_decimal_or_none(raw.get("min_order_size")),
        tick_size=_decimal_or_none(raw.get("tick_size")),
        neg_risk=_bool_or_none(raw.get("neg_risk")),
        last_trade_price=_decimal_or_none(raw.get("last_trade_price")),
        bids=_normalize_levels(raw.get("bids", []), OrderBookSide.BID),
        asks=_normalize_levels(raw.get("asks", []), OrderBookSide.ASK),
        raw_payload=raw,
    )


def normalize_public_trade(raw: dict[str, Any]) -> Trade:
    traded_at = normalize_datetime(raw.get("timestamp")) or datetime.now(UTC)
    condition_id = _string(raw.get("conditionId") or raw.get("market"))
    asset_id = _string(raw.get("asset") or raw.get("asset_id"))
    transaction_hash = _string(raw.get("transactionHash") or raw.get("transaction_hash"))
    trade_id = _string(raw.get("id")) or _stable_hash(
        [
            transaction_hash or "",
            condition_id or "",
            asset_id or "",
            str(raw.get("side") or ""),
            str(raw.get("price") or ""),
            str(raw.get("size") or ""),
            str(raw.get("timestamp") or ""),
        ]
    )

    return Trade(
        trade_id=trade_id,
        condition_id=condition_id,
        asset_id=asset_id,
        side=_string(raw.get("side")),
        price=_decimal_or_none(raw.get("price")) or Decimal("0"),
        size=_decimal_or_none(raw.get("size")) or Decimal("0"),
        traded_at=traded_at,
        outcome=_string(raw.get("outcome")),
        outcome_index=_int_or_none(raw.get("outcomeIndex") or raw.get("outcome_index")),
        transaction_hash=transaction_hash,
        proxy_wallet=_string(raw.get("proxyWallet") or raw.get("proxy_wallet")),
        title=_string(raw.get("title")),
        slug=_string(raw.get("slug")),
        raw_payload=raw,
    )


def normalize_price_ticks(
    asset_id: str,
    raw: dict[str, Any],
    source: str = "clob_prices_history",
) -> list[PriceTick]:
    ticks: list[PriceTick] = []
    for item in raw.get("history", []):
        if not isinstance(item, dict):
            continue
        timestamp = item.get("t")
        price = _decimal_or_none(item.get("p"))
        if timestamp is None or price is None:
            continue
        ticks.append(
            PriceTick(
                asset_id=asset_id,
                ts=normalize_unix_timestamp(timestamp),
                price=price,
                source=source,
                raw_payload=item,
            )
        )
    return ticks


def _normalize_levels(raw_levels: Any, side: OrderBookSide) -> list[OrderBookLevel]:
    if not isinstance(raw_levels, list):
        return []
    levels: list[OrderBookLevel] = []
    for index, item in enumerate(raw_levels):
        if not isinstance(item, dict):
            continue
        price = _decimal_or_none(item.get("price"))
        size = _decimal_or_none(item.get("size"))
        if price is None or size is None:
            continue
        levels.append(OrderBookLevel(side=side, price=price, size=size, level_index=index))
    return levels


def _parse_jsonish(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return [part.strip() for part in stripped.split(",") if part.strip()]
        return parsed if isinstance(parsed, list) else []
    return []


def _extract_tags(raw: dict[str, Any]) -> list[str]:
    tags = raw.get("tags")
    if isinstance(tags, list):
        return [str(tag.get("label") or tag.get("slug") or tag) for tag in tags]
    return []


def _extract_event_slug(raw: dict[str, Any]) -> str | None:
    events = raw.get("events")
    if isinstance(events, list) and events and isinstance(events[0], dict):
        return _string(events[0].get("slug"))
    return None


def _safe_list_get(values: list[Any], index: int) -> str | None:
    if index >= len(values):
        return None
    return _string(values[index])


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _string(value: Any) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


def _stable_hash(parts: list[str]) -> str:
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()

