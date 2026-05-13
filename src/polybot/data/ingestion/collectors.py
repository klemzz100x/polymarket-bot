from collections.abc import Sequence
from datetime import datetime

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from polybot.core.logging import get_logger
from polybot.data.ingestion.health import CollectorHeartbeat
from polybot.data.ingestion.retry import RetryPolicy, run_with_retry
from polybot.data.normalization import (
    normalize_market,
    normalize_orderbook,
    normalize_price_ticks,
    normalize_public_trade,
)
from polybot.data.normalization.time import utc_now
from polybot.data.schemas import DataIngestionLog, Market, OrderBookSnapshot, PriceTick, Trade
from polybot.data.storage.redis_cache import MarketRedisCache
from polybot.data.storage.repositories import (
    IngestionLogRepository,
    MarketRepository,
    OrderBookRepository,
    PriceTickRepository,
    RawPayloadRepository,
    TradeRepository,
)
from polybot.monitoring import record_collector_run
from polybot.polymarket.api import PolymarketClient

logger = get_logger(__name__)


class PolymarketDataCollector:
    def __init__(
        self,
        client: PolymarketClient,
        session: AsyncSession | None = None,
        redis: Redis | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.client = client
        self.session = session
        self.cache = MarketRedisCache(redis) if redis else None
        self.retry_policy = retry_policy or RetryPolicy()
        self.heartbeat = CollectorHeartbeat(collector_name="polymarket_data_collector")

    async def collect_markets(
        self,
        *,
        active: bool | None = True,
        closed: bool | None = False,
        limit: int | None = None,
        offset: int = 0,
        enable_order_book: bool | None = None,
        persist: bool = True,
    ) -> list[Market]:
        started_at = utc_now()
        try:
            raw_markets = await run_with_retry(
                lambda: self.client.list_markets(
                    active=active,
                    closed=closed,
                    limit=limit,
                    offset=offset,
                    enable_order_book=enable_order_book,
                ),
                policy=self.retry_policy,
                operation_name="collect_markets",
            )
        except Exception as exc:
            await self._record_failure("collect_markets", started_at=started_at, error=exc)
            raise
        markets = [normalize_market(item) for item in raw_markets]

        written = 0
        if persist and self.session:
            raw_result = await RawPayloadRepository(self.session).insert_many(
                source="polymarket_gamma",
                endpoint="/markets",
                payloads=raw_markets,
            )
            result = await MarketRepository(self.session).upsert_many(markets)
            written = result.written
            finished_at = utc_now()
            await self._log(
                DataIngestionLog(
                    source="polymarket_gamma",
                    job_type="collect_markets",
                    status="success",
                    started_at=started_at,
                    finished_at=finished_at,
                    rows_seen=raw_result.seen,
                    rows_written=written,
                    metadata={"offset": offset, "limit": limit or len(raw_markets)},
                )
            )
            await self.session.commit()
        else:
            finished_at = utc_now()

        if self.cache:
            await self.cache.cache_active_markets(markets)

        self._record_success(
            "collect_markets",
            rows_seen=len(raw_markets),
            rows_written=written,
            started_at=started_at,
            finished_at=finished_at,
        )
        logger.info("markets_collected", seen=len(raw_markets), written=written)
        return markets

    async def collect_orderbooks(
        self,
        *,
        token_ids: Sequence[str],
        persist: bool = True,
    ) -> list[OrderBookSnapshot]:
        started_at = utc_now()
        received_at = utc_now()
        try:
            raw_books = await run_with_retry(
                lambda: self.client.get_orderbooks(token_ids),
                policy=self.retry_policy,
                operation_name="collect_orderbooks",
            )
        except Exception as exc:
            await self._record_failure("collect_orderbooks", started_at=started_at, error=exc)
            raise
        snapshots = [normalize_orderbook(item, received_at=received_at) for item in raw_books]

        written = 0
        if persist and self.session:
            await RawPayloadRepository(self.session).insert_many(
                source="polymarket_clob",
                endpoint="/books",
                payloads=raw_books,
                external_id_key="asset_id",
            )
            result = await OrderBookRepository(self.session).insert_many(snapshots)
            written = result.written
            finished_at = utc_now()
            await self._log(
                DataIngestionLog(
                    source="polymarket_clob",
                    job_type="collect_orderbooks",
                    status="success",
                    started_at=started_at,
                    finished_at=finished_at,
                    rows_seen=len(raw_books),
                    rows_written=written,
                    metadata={"token_ids": list(token_ids)},
                )
            )
            await self.session.commit()
        else:
            finished_at = utc_now()

        if self.cache:
            for snapshot in snapshots:
                await self.cache.cache_orderbook(snapshot)

        self._record_success(
            "collect_orderbooks",
            rows_seen=len(raw_books),
            rows_written=written,
            started_at=started_at,
            finished_at=finished_at,
        )
        logger.info("orderbooks_collected", seen=len(raw_books), written=written)
        return snapshots

    async def collect_trades(
        self,
        *,
        markets: Sequence[str] | None = None,
        limit: int = 100,
        offset: int = 0,
        persist: bool = True,
    ) -> list[Trade]:
        started_at = utc_now()
        try:
            raw_trades = await run_with_retry(
                lambda: self.client.get_public_trades(
                    markets=markets,
                    limit=limit,
                    offset=offset,
                ),
                policy=self.retry_policy,
                operation_name="collect_trades",
            )
        except Exception as exc:
            await self._record_failure("collect_trades", started_at=started_at, error=exc)
            raise
        trades = [normalize_public_trade(item) for item in raw_trades]

        written = 0
        if persist and self.session:
            await RawPayloadRepository(self.session).insert_many(
                source="polymarket_data",
                endpoint="/trades",
                payloads=raw_trades,
                external_id_key="transactionHash",
            )
            result = await TradeRepository(self.session).upsert_many(trades)
            written = result.written
            finished_at = utc_now()
            await self._log(
                DataIngestionLog(
                    source="polymarket_data",
                    job_type="collect_trades",
                    status="success",
                    started_at=started_at,
                    finished_at=finished_at,
                    rows_seen=len(raw_trades),
                    rows_written=written,
                    metadata={"markets": list(markets or []), "offset": offset, "limit": limit},
                )
            )
            await self.session.commit()
        else:
            finished_at = utc_now()

        self._record_success(
            "collect_trades",
            rows_seen=len(raw_trades),
            rows_written=written,
            started_at=started_at,
            finished_at=finished_at,
        )
        logger.info("trades_collected", seen=len(raw_trades), written=written)
        return trades

    async def collect_price_history(
        self,
        *,
        token_id: str,
        start_ts: int | None = None,
        end_ts: int | None = None,
        interval: str | None = None,
        fidelity: int | None = None,
        persist: bool = True,
    ) -> list[PriceTick]:
        started_at = utc_now()
        try:
            raw_history = await run_with_retry(
                lambda: self.client.get_price_history(
                    token_id=token_id,
                    start_ts=start_ts,
                    end_ts=end_ts,
                    interval=interval,
                    fidelity=fidelity,
                ),
                policy=self.retry_policy,
                operation_name="collect_price_history",
            )
        except Exception as exc:
            await self._record_failure("collect_price_history", started_at=started_at, error=exc)
            raise
        ticks = normalize_price_ticks(token_id, raw_history)

        written = 0
        if persist and self.session:
            result = await PriceTickRepository(self.session).upsert_many(ticks)
            written = result.written
            finished_at = utc_now()
            await self._log(
                DataIngestionLog(
                    source="polymarket_clob",
                    job_type="collect_price_history",
                    status="success",
                    started_at=started_at,
                    finished_at=finished_at,
                    rows_seen=len(ticks),
                    rows_written=written,
                    metadata={"token_id": token_id, "interval": interval, "fidelity": fidelity},
                )
            )
            await self.session.commit()
        else:
            finished_at = utc_now()

        self._record_success(
            "collect_price_history",
            rows_seen=len(ticks),
            rows_written=written,
            started_at=started_at,
            finished_at=finished_at,
        )
        logger.info("price_history_collected", token_id=token_id, seen=len(ticks), written=written)
        return ticks

    async def _log(self, log: DataIngestionLog) -> None:
        if self.session:
            await IngestionLogRepository(self.session).insert(log)

    def _record_success(
        self,
        job_type: str,
        *,
        rows_seen: int,
        rows_written: int,
        started_at: datetime,
        finished_at: datetime,
    ) -> None:
        self.heartbeat.record_success(
            rows_seen=rows_seen,
            rows_written=rows_written,
            timestamp=finished_at,
        )
        record_collector_run(
            job_type=job_type,
            status="success",
            rows_seen=rows_seen,
            rows_written=rows_written,
            started_at=started_at,
            finished_at=finished_at,
        )

    async def _record_failure(
        self,
        job_type: str,
        *,
        started_at: datetime,
        error: Exception,
    ) -> None:
        finished_at = utc_now()
        self.heartbeat.record_failure(error=error, timestamp=finished_at)
        record_collector_run(
            job_type=job_type,
            status="failure",
            rows_seen=0,
            rows_written=0,
            started_at=started_at,
            finished_at=finished_at,
        )
        if self.session:
            await self._log(
                DataIngestionLog(
                    source="polymarket",
                    job_type=job_type,
                    status="failure",
                    started_at=started_at,
                    finished_at=finished_at,
                    rows_seen=0,
                    rows_written=0,
                    error_message=str(error),
                    metadata={},
                )
            )
            await self.session.commit()
