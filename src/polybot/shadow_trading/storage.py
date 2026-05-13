from dataclasses import asdict

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from polybot.shadow_trading.models import ShadowTradingResult, _json_ready


class ShadowTradingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_result(self, result: ShadowTradingResult) -> None:
        stmt = text(
            """
                INSERT INTO app.shadow_trading_runs (
                    id, market_id, strategy_name, started_at, finished_at,
                    snapshot_count, signal_count, decision_count, theoretical_fill_count,
                    missed_fill_count, impossible_fill_count, average_slippage,
                    average_delay_ms, fill_probability, result
                )
                VALUES (
                    :id, :market_id, :strategy_name, :started_at, :finished_at,
                    :snapshot_count, :signal_count, :decision_count, :theoretical_fill_count,
                    :missed_fill_count, :impossible_fill_count, :average_slippage,
                    :average_delay_ms, :fill_probability, CAST(:result AS JSONB)
                )
                ON CONFLICT (id) DO UPDATE SET
                    finished_at = EXCLUDED.finished_at,
                    snapshot_count = EXCLUDED.snapshot_count,
                    signal_count = EXCLUDED.signal_count,
                    decision_count = EXCLUDED.decision_count,
                    theoretical_fill_count = EXCLUDED.theoretical_fill_count,
                    missed_fill_count = EXCLUDED.missed_fill_count,
                    impossible_fill_count = EXCLUDED.impossible_fill_count,
                    average_slippage = EXCLUDED.average_slippage,
                    average_delay_ms = EXCLUDED.average_delay_ms,
                    fill_probability = EXCLUDED.fill_probability,
                    result = EXCLUDED.result
                """
        ).bindparams(bindparam("result", type_=JSONB))
        await self.session.execute(
            stmt,
            {
                "id": result.run_id,
                "market_id": result.market_id,
                "strategy_name": result.strategy_name,
                "started_at": result.started_at,
                "finished_at": result.finished_at,
                "snapshot_count": result.snapshot_count,
                "signal_count": result.signal_count,
                "decision_count": result.decision_count,
                "theoretical_fill_count": result.theoretical_fill_count,
                "missed_fill_count": result.missed_fill_count,
                "impossible_fill_count": result.impossible_fill_count,
                "average_slippage": result.average_slippage,
                "average_delay_ms": result.average_delay_ms,
                "fill_probability": result.fill_probability,
                "result": result.to_dict(),
            },
        )
        fills_by_order = {fill.order_id: fill for fill in result.fills}
        comparisons_by_order = {item.order_id: item for item in result.comparisons}
        for decision in result.decisions:
            fill = fills_by_order.get(decision.order.order_id)
            comparison = comparisons_by_order.get(decision.order.order_id)
            stmt = text(
                """
                    INSERT INTO app.shadow_trading_decisions (
                        run_id, decision_id, decision_ts, market_id, asset_id, signal_type,
                        action, status, order_json, fill_json, comparison_json
                    )
                    VALUES (
                        :run_id, :decision_id, :decision_ts, :market_id, :asset_id, :signal_type,
                        :action, :status, CAST(:order_json AS JSONB), CAST(:fill_json AS JSONB),
                        CAST(:comparison_json AS JSONB)
                    )
                    ON CONFLICT (decision_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        fill_json = EXCLUDED.fill_json,
                        comparison_json = EXCLUDED.comparison_json
                    """
            ).bindparams(
                bindparam("order_json", type_=JSONB),
                bindparam("fill_json", type_=JSONB),
                bindparam("comparison_json", type_=JSONB),
            )
            await self.session.execute(
                stmt,
                {
                    "run_id": result.run_id,
                    "decision_id": decision.decision_id,
                    "decision_ts": decision.timestamp,
                    "market_id": decision.market_id,
                    "asset_id": decision.asset_id,
                    "signal_type": decision.signal_type,
                    "action": decision.action,
                    "status": decision.status,
                    "order_json": _json_obj(decision.order),
                    "fill_json": _json_obj(fill) if fill else {},
                    "comparison_json": _json_obj(comparison) if comparison else {},
                },
            )

    async def latest_result(self) -> dict | None:
        row = (
            await self.session.execute(
                text(
                    """
                    SELECT *
                    FROM app.shadow_trading_runs
                    ORDER BY started_at DESC
                    LIMIT 1
                    """
                )
            )
        ).mappings().first()
        return dict(row) if row else None


def _json_obj(value) -> dict:
    return _json_ready(asdict(value))
