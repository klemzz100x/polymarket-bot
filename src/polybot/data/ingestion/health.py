from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from polybot.data.normalization.time import utc_now
from polybot.data.schemas import OrderBookSnapshot


@dataclass(slots=True)
class CollectorHeartbeat:
    collector_name: str
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_error: str | None = None
    successful_runs: int = 0
    failed_runs: int = 0
    last_rows_seen: int = 0
    last_rows_written: int = 0

    def record_success(
        self,
        *,
        rows_seen: int,
        rows_written: int,
        timestamp: datetime | None = None,
    ) -> None:
        self.last_success_at = timestamp or utc_now()
        self.last_error = None
        self.successful_runs += 1
        self.last_rows_seen = rows_seen
        self.last_rows_written = rows_written

    def record_failure(self, *, error: Exception, timestamp: datetime | None = None) -> None:
        self.last_failure_at = timestamp or utc_now()
        self.last_error = str(error)
        self.failed_runs += 1

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class StaleSnapshot:
    asset_id: str
    condition_id: str
    snapshot_ts: datetime
    age_seconds: Decimal

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class CollectorHealthReport:
    collector_name: str
    generated_at: datetime
    heartbeat: dict[str, Any]
    stale_snapshots: list[StaleSnapshot] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.heartbeat.get("last_error"):
            return "warning"
        if self.stale_snapshots:
            return "warning"
        return "ok"

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self) | {"status": self.status})


def detect_stale_snapshots(
    snapshots: list[OrderBookSnapshot],
    *,
    now: datetime | None = None,
    max_age_seconds: int = 30,
) -> list[StaleSnapshot]:
    current = now or utc_now()
    stale: list[StaleSnapshot] = []
    latest_by_asset: dict[str, OrderBookSnapshot] = {}
    for snapshot in snapshots:
        current_latest = latest_by_asset.get(snapshot.asset_id)
        if current_latest is None or snapshot.snapshot_ts > current_latest.snapshot_ts:
            latest_by_asset[snapshot.asset_id] = snapshot

    for snapshot in latest_by_asset.values():
        age = Decimal(str((current - snapshot.snapshot_ts).total_seconds()))
        if age > Decimal(max_age_seconds):
            stale.append(
                StaleSnapshot(
                    asset_id=snapshot.asset_id,
                    condition_id=snapshot.condition_id,
                    snapshot_ts=snapshot.snapshot_ts,
                    age_seconds=age,
                )
            )
    return stale


def build_collector_health_report(
    heartbeat: CollectorHeartbeat,
    *,
    snapshots: list[OrderBookSnapshot] | None = None,
    max_age_seconds: int = 30,
) -> CollectorHealthReport:
    return CollectorHealthReport(
        collector_name=heartbeat.collector_name,
        generated_at=utc_now(),
        heartbeat=heartbeat.to_dict(),
        stale_snapshots=detect_stale_snapshots(
            snapshots or [],
            max_age_seconds=max_age_seconds,
        ),
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
