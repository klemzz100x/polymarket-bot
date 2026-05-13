import json
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from polybot.paper_trading.equity import PaperEquitySnapshot


class PaperEquityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_snapshots(self, snapshots: list[PaperEquitySnapshot]) -> None:
        for snapshot in snapshots:
            await self.session.execute(
                text(
                    """
                    INSERT INTO app.paper_equity_snapshots (
                        run_id, market_id, strategy_name, snapshot_ts, equity, cash,
                        net_pnl, exposure, positions, source
                    )
                    VALUES (
                        :run_id, :market_id, :strategy_name, :snapshot_ts, :equity, :cash,
                        :net_pnl, :exposure, CAST(:positions AS JSONB), :source
                    )
                    ON CONFLICT (run_id, snapshot_ts, source) DO UPDATE SET
                        equity = EXCLUDED.equity,
                        cash = EXCLUDED.cash,
                        net_pnl = EXCLUDED.net_pnl,
                        exposure = EXCLUDED.exposure,
                        positions = EXCLUDED.positions
                    """
                ),
                {
                    "run_id": snapshot.run_id,
                    "market_id": snapshot.market_id,
                    "strategy_name": snapshot.strategy_name,
                    "snapshot_ts": snapshot.snapshot_ts,
                    "equity": snapshot.equity,
                    "cash": snapshot.cash,
                    "net_pnl": snapshot.net_pnl,
                    "exposure": snapshot.exposure,
                    "positions": json.dumps(snapshot.positions),
                    "source": snapshot.source,
                },
            )

    async def latest_equity(
        self,
        *,
        strategy_name: str | None = None,
        market_id: str | None = None,
    ) -> dict[str, Any] | None:
        filters = []
        params: dict[str, Any] = {}
        if strategy_name:
            filters.append("strategy_name = :strategy_name")
            params["strategy_name"] = strategy_name
        if market_id:
            filters.append("market_id = :market_id")
            params["market_id"] = market_id
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        row = (
            await self.session.execute(
                text(
                    f"""
                    SELECT run_id, market_id, strategy_name, snapshot_ts, equity, cash,
                           net_pnl, exposure, positions, source
                    FROM app.paper_equity_snapshots
                    {where}
                    ORDER BY snapshot_ts DESC, id DESC
                    LIMIT 1
                    """
                ),
                params,
            )
        ).mappings().first()
        return dict(row) if row else None

    async def list_equity(
        self,
        *,
        strategy_name: str | None = None,
        market_id: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        filters = []
        params: dict[str, Any] = {"limit": limit}
        if strategy_name:
            filters.append("strategy_name = :strategy_name")
            params["strategy_name"] = strategy_name
        if market_id:
            filters.append("market_id = :market_id")
            params["market_id"] = market_id
        if start:
            filters.append("snapshot_ts >= :start")
            params["start"] = start
        if end:
            filters.append("snapshot_ts <= :end")
            params["end"] = end
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        rows = await self.session.execute(
            text(
                f"""
                SELECT run_id, market_id, strategy_name, snapshot_ts, equity, cash,
                       net_pnl, exposure, positions, source
                FROM app.paper_equity_snapshots
                {where}
                ORDER BY snapshot_ts ASC
                LIMIT :limit
                """
            ),
            params,
        )
        return [dict(row) for row in rows.mappings().all()]

    async def live_performance(self) -> dict[str, Any]:
        rows = await self.session.execute(
            text(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (strategy_name, market_id)
                        strategy_name, market_id, snapshot_ts, equity, net_pnl, exposure
                    FROM app.paper_equity_snapshots
                    ORDER BY strategy_name, market_id, snapshot_ts DESC, id DESC
                )
                SELECT
                    COUNT(*) AS tracked_pairs,
                    COALESCE(SUM(net_pnl), 0) AS net_pnl,
                    COALESCE(SUM(exposure), 0) AS exposure,
                    MAX(snapshot_ts) AS latest_snapshot_ts
                FROM latest
                """
            )
        )
        summary = dict(rows.mappings().first() or {})
        run_rows = await self.session.execute(
            text(
                """
                SELECT
                    COUNT(*) AS paper_runs,
                    COALESCE(SUM(filled_orders), 0) AS filled_orders,
                    COALESCE(SUM(rejected_orders), 0) AS rejected_orders
                FROM app.paper_trading_runs
                """
            )
        )
        summary.update(dict(run_rows.mappings().first() or {}))
        return summary
