#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
import json

from polybot.backtesting import MarketReplay
from polybot.core.config import get_settings
from polybot.data.schemas import OrderBookLevel, OrderBookSnapshot
from polybot.data.schemas.orderbook import OrderBookSide
from polybot.data.storage.database import create_session_factory
from polybot.data.storage.repositories import OrderBookRepository


async def run() -> int:
    parser = argparse.ArgumentParser(description="Replay stored orderbook snapshots.")
    parser.add_argument("--asset-id")
    parser.add_argument("--condition-id")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--jsonl", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    session_factory = create_session_factory(settings.database_url)
    async with session_factory() as session:
        rows = await OrderBookRepository(session).list_snapshots(
            asset_id=args.asset_id,
            condition_id=args.condition_id,
            limit=args.limit,
        )

    snapshots = [_to_snapshot(row) for row in rows]
    for event in MarketReplay(snapshots):
        payload = event.snapshot.model_dump(mode="json")
        payload["sequence"] = event.sequence
        if args.jsonl:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(
                f"#{event.sequence} {event.snapshot.snapshot_ts.isoformat()} "
                f"{event.snapshot.asset_id} bid={event.snapshot.best_bid} "
                f"ask={event.snapshot.best_ask} spread={event.snapshot.spread}"
            )
    return 0


def _to_snapshot(row: object) -> OrderBookSnapshot:
    levels = [
        OrderBookLevel(
            side=OrderBookSide(level.side),
            price=level.price,
            size=level.size,
            level_index=level.level_index,
        )
        for level in row.levels
    ]
    bids = sorted([level for level in levels if level.side == OrderBookSide.BID], key=lambda x: x.level_index)
    asks = sorted([level for level in levels if level.side == OrderBookSide.ASK], key=lambda x: x.level_index)
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


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))

