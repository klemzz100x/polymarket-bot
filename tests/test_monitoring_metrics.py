from datetime import datetime
from polybot.core.compat import UTC

from polybot.monitoring import record_collector_run, record_stale_snapshots


def test_monitoring_metric_helpers_do_not_raise() -> None:
    started_at = datetime(2026, 1, 1, tzinfo=UTC)
    finished_at = datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC)

    record_collector_run(
        job_type="test_collector",
        status="success",
        rows_seen=2,
        rows_written=1,
        started_at=started_at,
        finished_at=finished_at,
    )
    record_stale_snapshots(job_type="test_collector", count=1)

    assert True
