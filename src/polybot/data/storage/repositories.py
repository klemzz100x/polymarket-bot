from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from polybot.data.schemas import DataIngestionLog, Market, OrderBookSnapshot, PriceTick, Trade
from polybot.data.storage.models import (
    DataIngestionLogORM,
    MarketORM,
    MarketOutcomeORM,
    OrderBookLevelORM,
    OrderBookSnapshotORM,
    PriceTickORM,
    RawApiPayloadORM,
    TradeORM,
)


@dataclass(frozen=True, slots=True)
class WriteResult:
    seen: int
    written: int


class MarketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_many(self, markets: Iterable[Market]) -> WriteResult:
        items = list(markets)
        for market in items:
            values = {
                "id": market.market_id,
                "condition_id": market.condition_id,
                "question": market.question,
                "slug": market.slug,
                "active": market.active,
                "closed": market.closed,
                "archived": market.archived,
                "accepting_orders": market.accepting_orders,
                "enable_order_book": market.enable_order_book,
                "category": market.category,
                "volume": market.volume,
                "liquidity": market.liquidity,
                "start_date": market.start_date,
                "end_date": market.end_date,
                "source_created_at": market.created_at,
                "source_updated_at": market.updated_at,
                "raw_payload": market.raw_payload,
            }
            stmt = insert(MarketORM).values(**values)
            await self.session.execute(
                stmt.on_conflict_do_update(
                    index_elements=[MarketORM.id],
                    set_={key: value for key, value in values.items() if key != "id"},
                )
            )

            for outcome in market.outcomes:
                outcome_values = {
                    "market_id": market.market_id,
                    "condition_id": outcome.condition_id,
                    "outcome_index": outcome.outcome_index,
                    "name": outcome.name,
                    "asset_id": outcome.asset_id,
                    "price": outcome.price,
                    "raw_payload": outcome.raw_payload,
                }
                outcome_stmt = insert(MarketOutcomeORM).values(**outcome_values)
                await self.session.execute(
                    outcome_stmt.on_conflict_do_update(
                        constraint="uq_market_outcome_index",
                        set_={
                            key: value
                            for key, value in outcome_values.items()
                            if key not in {"market_id", "outcome_index"}
                        },
                    )
                )
        return WriteResult(seen=len(items), written=len(items))

    async def active_asset_ids(self, limit: int | None = None) -> list[str]:
        stmt: Select[tuple[str]] = (
            select(MarketOutcomeORM.asset_id)
            .join(MarketORM, MarketORM.id == MarketOutcomeORM.market_id)
            .where(MarketORM.active.is_(True), MarketORM.closed.is_(False))
            .where(MarketOutcomeORM.asset_id.is_not(None))
            .order_by(MarketORM.updated_at.desc())
        )
        if limit:
            stmt = stmt.limit(limit)
        rows = await self.session.execute(stmt)
        return [row[0] for row in rows if row[0]]

    async def asset_ids_for_market(self, market_id_or_condition_id: str) -> list[str]:
        stmt = (
            select(MarketOutcomeORM.asset_id)
            .join(MarketORM, MarketORM.id == MarketOutcomeORM.market_id)
            .where(
                (MarketORM.id == market_id_or_condition_id)
                | (MarketORM.condition_id == market_id_or_condition_id)
            )
            .where(MarketOutcomeORM.asset_id.is_not(None))
        )
        rows = await self.session.execute(stmt)
        return [row[0] for row in rows if row[0]]


class OrderBookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_many(self, snapshots: Iterable[OrderBookSnapshot]) -> WriteResult:
        items = list(snapshots)
        written = 0
        for snapshot in items:
            values = {
                "condition_id": snapshot.condition_id,
                "asset_id": snapshot.asset_id,
                "snapshot_ts": snapshot.snapshot_ts,
                "received_at": snapshot.received_at,
                "book_hash": snapshot.book_hash,
                "min_order_size": snapshot.min_order_size,
                "tick_size": snapshot.tick_size,
                "neg_risk": snapshot.neg_risk,
                "last_trade_price": snapshot.last_trade_price,
                "raw_payload": snapshot.raw_payload,
            }
            stmt = insert(OrderBookSnapshotORM).values(**values)
            result = await self.session.execute(
                stmt.on_conflict_do_nothing(
                    constraint="uq_orderbook_asset_ts_hash",
                ).returning(OrderBookSnapshotORM.id)
            )
            snapshot_id = result.scalar_one_or_none()
            if snapshot_id is None:
                continue
            written += 1

            levels = [*snapshot.bids, *snapshot.asks]
            if levels:
                await self.session.execute(
                    insert(OrderBookLevelORM),
                    [
                        {
                            "snapshot_id": snapshot_id,
                            "side": level.side.value,
                            "price": level.price,
                            "size": level.size,
                            "level_index": level.level_index,
                        }
                        for level in levels
                    ],
                )
        return WriteResult(seen=len(items), written=written)

    async def list_snapshots(
        self,
        *,
        asset_id: str | None = None,
        condition_id: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 100,
    ) -> list[OrderBookSnapshotORM]:
        stmt = (
            select(OrderBookSnapshotORM)
            .options(selectinload(OrderBookSnapshotORM.levels))
            .order_by(OrderBookSnapshotORM.snapshot_ts.asc())
            .limit(limit)
        )
        if asset_id:
            stmt = stmt.where(OrderBookSnapshotORM.asset_id == asset_id)
        if condition_id:
            stmt = stmt.where(OrderBookSnapshotORM.condition_id == condition_id)
        if start:
            stmt = stmt.where(OrderBookSnapshotORM.snapshot_ts >= start)
        if end:
            stmt = stmt.where(OrderBookSnapshotORM.snapshot_ts <= end)
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())


class TradeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_many(self, trades: Iterable[Trade]) -> WriteResult:
        items = list(trades)
        if not items:
            return WriteResult(seen=0, written=0)
        values = [
            {
                "id": trade.trade_id,
                "condition_id": trade.condition_id,
                "asset_id": trade.asset_id,
                "side": trade.side,
                "price": trade.price,
                "size": trade.size,
                "traded_at": trade.traded_at,
                "outcome": trade.outcome,
                "outcome_index": trade.outcome_index,
                "transaction_hash": trade.transaction_hash,
                "proxy_wallet": trade.proxy_wallet,
                "title": trade.title,
                "slug": trade.slug,
                "raw_payload": trade.raw_payload,
            }
            for trade in items
        ]
        stmt = insert(TradeORM).values(values)
        await self.session.execute(
            stmt.on_conflict_do_update(
                index_elements=[TradeORM.id],
                set_={key: stmt.excluded[key] for key in values[0] if key != "id"},
            )
        )
        return WriteResult(seen=len(items), written=len(items))

    async def list_trades(
        self,
        *,
        condition_id: str | None = None,
        asset_id: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 1000,
    ) -> list[TradeORM]:
        stmt = select(TradeORM).order_by(TradeORM.traded_at.asc()).limit(limit)
        if condition_id:
            stmt = stmt.where(TradeORM.condition_id == condition_id)
        if asset_id:
            stmt = stmt.where(TradeORM.asset_id == asset_id)
        if start:
            stmt = stmt.where(TradeORM.traded_at >= start)
        if end:
            stmt = stmt.where(TradeORM.traded_at <= end)
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())


class PriceTickRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_many(self, ticks: Iterable[PriceTick]) -> WriteResult:
        items = list(ticks)
        if not items:
            return WriteResult(seen=0, written=0)
        values = [
            {
                "asset_id": tick.asset_id,
                "ts": tick.ts,
                "price": tick.price,
                "source": tick.source,
                "raw_payload": tick.raw_payload,
            }
            for tick in items
        ]
        stmt = insert(PriceTickORM).values(values)
        await self.session.execute(
            stmt.on_conflict_do_update(
                constraint="uq_price_tick_asset_ts_source",
                set_={"price": stmt.excluded.price, "raw_payload": stmt.excluded.raw_payload},
            )
        )
        return WriteResult(seen=len(items), written=len(items))

    async def list_ticks(
        self,
        *,
        asset_id: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 5000,
    ) -> list[PriceTickORM]:
        stmt = select(PriceTickORM).order_by(PriceTickORM.ts.asc()).limit(limit)
        if asset_id:
            stmt = stmt.where(PriceTickORM.asset_id == asset_id)
        if start:
            stmt = stmt.where(PriceTickORM.ts >= start)
        if end:
            stmt = stmt.where(PriceTickORM.ts <= end)
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())


class IngestionLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert(self, log: DataIngestionLog) -> None:
        self.session.add(
            DataIngestionLogORM(
                source=log.source,
                job_type=log.job_type,
                status=log.status,
                started_at=log.started_at,
                finished_at=log.finished_at,
                rows_seen=log.rows_seen,
                rows_written=log.rows_written,
                error_message=log.error_message,
                metadata_json=log.metadata,
            )
        )


class RawPayloadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_many(
        self,
        *,
        source: str,
        endpoint: str,
        payloads: Iterable[dict[str, object]],
        external_id_key: str = "id",
    ) -> WriteResult:
        items = list(payloads)
        if not items:
            return WriteResult(seen=0, written=0)
        values = [
            {
                "source": source,
                "endpoint": endpoint,
                "external_id": str(item.get(external_id_key)) if item.get(external_id_key) else None,
                "payload": item,
            }
            for item in items
        ]
        stmt = insert(RawApiPayloadORM).values(values)
        await self.session.execute(
            stmt.on_conflict_do_update(
                constraint="uq_raw_api_payload_external",
                set_={"payload": stmt.excluded.payload},
            )
        )
        return WriteResult(seen=len(items), written=len(items))
