import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from polybot.paper_trading.equity import build_equity_snapshots
from polybot.paper_trading.equity_storage import PaperEquityRepository
from polybot.paper_trading.models import PaperTradingResult


class PaperTradingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_result(self, result: PaperTradingResult) -> None:
        await self.session.execute(
            text(
                """
                INSERT INTO app.paper_trading_runs (
                    id, market_id, strategy_name, decision_mode, started_at, finished_at,
                    snapshot_count, signal_count, attempted_orders, filled_orders, rejected_orders,
                    final_cash, final_equity, net_pnl, fees, result
                )
                VALUES (
                    :id, :market_id, :strategy_name, :decision_mode, :started_at, :finished_at,
                    :snapshot_count, :signal_count, :attempted_orders, :filled_orders, :rejected_orders,
                    :final_cash, :final_equity, :net_pnl, :fees, CAST(:result AS JSONB)
                )
                ON CONFLICT (id) DO UPDATE SET
                    finished_at = EXCLUDED.finished_at,
                    snapshot_count = EXCLUDED.snapshot_count,
                    signal_count = EXCLUDED.signal_count,
                    attempted_orders = EXCLUDED.attempted_orders,
                    filled_orders = EXCLUDED.filled_orders,
                    rejected_orders = EXCLUDED.rejected_orders,
                    final_cash = EXCLUDED.final_cash,
                    final_equity = EXCLUDED.final_equity,
                    net_pnl = EXCLUDED.net_pnl,
                    fees = EXCLUDED.fees,
                    result = EXCLUDED.result
                """
            ),
            {
                "id": result.run_id,
                "market_id": result.market_id,
                "strategy_name": result.strategy_name,
                "decision_mode": str(result.metadata.get("decision_mode", "")),
                "started_at": result.started_at,
                "finished_at": result.finished_at,
                "snapshot_count": result.snapshot_count,
                "signal_count": result.signal_count,
                "attempted_orders": result.attempted_orders,
                "filled_orders": result.filled_orders,
                "rejected_orders": result.rejected_orders,
                "final_cash": result.final_cash,
                "final_equity": result.final_equity,
                "net_pnl": result.net_pnl,
                "fees": result.fees,
                "result": result.to_json(),
            },
        )
        for event in result.events:
            await self.session.execute(
                text(
                    """
                    INSERT INTO app.paper_trading_events (run_id, event_type, event_ts, payload)
                    VALUES (:run_id, :event_type, :event_ts, CAST(:payload AS JSONB))
                    """
                ),
                {
                    "run_id": result.run_id,
                    "event_type": event.event_type,
                    "event_ts": event.timestamp,
                    "payload": json.dumps(event.to_dict()["payload"], default=str),
                },
            )
        await PaperEquityRepository(self.session).insert_snapshots(build_equity_snapshots(result))
