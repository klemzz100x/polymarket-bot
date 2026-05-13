from polybot.data.schemas import OrderBookLevel, OrderBookSnapshot, PriceTick, Trade
from polybot.data.schemas.orderbook import OrderBookSide
from polybot.data.storage.models import (
    OrderBookSnapshotORM,
    PriceTickORM,
    TradeORM,
)


def orderbook_snapshot_from_orm(row: OrderBookSnapshotORM) -> OrderBookSnapshot:
    levels = [
        OrderBookLevel(
            side=OrderBookSide(level.side),
            price=level.price,
            size=level.size,
            level_index=level.level_index,
        )
        for level in row.levels
    ]
    bids = sorted(
        [level for level in levels if level.side == OrderBookSide.BID],
        key=lambda item: item.level_index,
    )
    asks = sorted(
        [level for level in levels if level.side == OrderBookSide.ASK],
        key=lambda item: item.level_index,
    )
    return OrderBookSnapshot(
        condition_id=row.condition_id,
        asset_id=row.asset_id,
        snapshot_ts=row.snapshot_ts,
        received_at=row.received_at,
        book_hash=row.book_hash,
        min_order_size=row.min_order_size,
        tick_size=row.tick_size,
        neg_risk=row.neg_risk,
        last_trade_price=row.last_trade_price,
        bids=bids,
        asks=asks,
        raw_payload=row.raw_payload,
    )


def trade_from_orm(row: TradeORM) -> Trade:
    return Trade(
        trade_id=row.id,
        condition_id=row.condition_id,
        asset_id=row.asset_id,
        side=row.side,
        price=row.price,
        size=row.size,
        traded_at=row.traded_at,
        outcome=row.outcome,
        outcome_index=row.outcome_index,
        transaction_hash=row.transaction_hash,
        proxy_wallet=row.proxy_wallet,
        title=row.title,
        slug=row.slug,
        raw_payload=row.raw_payload,
    )


def price_tick_from_orm(row: PriceTickORM) -> PriceTick:
    return PriceTick(
        asset_id=row.asset_id,
        ts=row.ts,
        price=row.price,
        source=row.source,
        raw_payload=row.raw_payload,
    )

