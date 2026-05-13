import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from polybot.live_execution.models import LiveOrder, RiskDecision


class LiveRiskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_risk_decision(self, order: LiveOrder, decision: RiskDecision) -> None:
        await self.session.execute(
            text(
                """
                INSERT INTO app.live_risk_events (
                    event_ts, client_order_id, market_id, asset_id,
                    strategy_name, allowed, reason, checks, metadata
                )
                VALUES (
                    now(), :client_order_id, :market_id, :asset_id,
                    :strategy_name, :allowed, :reason,
                    CAST(:checks AS JSONB), CAST(:metadata AS JSONB)
                )
                """
            ),
            {
                "client_order_id": order.client_order_id,
                "market_id": order.market_id,
                "asset_id": order.asset_id,
                "strategy_name": order.strategy_name,
                "allowed": decision.allowed,
                "reason": decision.reason,
                "checks": json.dumps(decision.checks, default=str),
                "metadata": json.dumps(decision.metadata, default=str),
            },
        )
