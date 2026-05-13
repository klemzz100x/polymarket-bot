import json

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from polybot.live_readiness.readiness_score import LiveReadinessReport
from polybot.risk.kill_switch import KillSwitchEvent


class LiveReadinessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_report(self, report: LiveReadinessReport) -> None:
        stmt = text(
            """
                INSERT INTO app.live_readiness_reports (
                    id, generated_at, status, live_readiness_score,
                    execution_quality_score, infrastructure_health_score,
                    strategy_stability_score, kill_switch_state, report
                )
                VALUES (
                    :id, :generated_at, :status, :live_readiness_score,
                    :execution_quality_score, :infrastructure_health_score,
                    :strategy_stability_score, :kill_switch_state, CAST(:report AS JSONB)
                )
                ON CONFLICT (id) DO UPDATE SET report = EXCLUDED.report
                """
        ).bindparams(bindparam("report", type_=JSONB))
        await self.session.execute(
            stmt,
            {
                "id": report.report_id,
                "generated_at": report.generated_at,
                "status": report.status,
                "live_readiness_score": report.live_readiness_score,
                "execution_quality_score": report.execution_quality_score,
                "infrastructure_health_score": report.infrastructure_health_score,
                "strategy_stability_score": report.strategy_stability_score,
                "kill_switch_state": report.kill_switch_state,
                "report": report.to_dict(),
            },
        )

    async def insert_kill_switch_events(self, events: list[KillSwitchEvent]) -> None:
        for event in events:
            stmt = text(
                """
                    INSERT INTO app.kill_switch_events (event_ts, state, trigger, severity, reason, metadata)
                    VALUES (:event_ts, :state, :trigger, :severity, :reason, CAST(:metadata AS JSONB))
                    """
            ).bindparams(bindparam("metadata", type_=JSONB))
            await self.session.execute(
                stmt,
                {
                    "event_ts": event.event_ts,
                    "state": event.state.value,
                    "trigger": event.trigger.value,
                    "severity": event.severity,
                    "reason": event.reason,
                    "metadata": json.loads(json.dumps(event.metadata, default=str)),
                },
            )

    async def latest_report(self) -> dict | None:
        row = (
            await self.session.execute(
                text(
                    """
                    SELECT *
                    FROM app.live_readiness_reports
                    ORDER BY generated_at DESC
                    LIMIT 1
                    """
                )
            )
        ).mappings().first()
        return dict(row) if row else None
