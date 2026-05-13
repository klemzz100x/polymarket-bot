from datetime import datetime

try:
    from prometheus_client import Counter, Gauge, Histogram
except ImportError:  # pragma: no cover - local smoke tests may run without optional deps.
    class _NoopMetric:
        def labels(self, **_labels: object) -> "_NoopMetric":
            return self

        def inc(self, _amount: float | int = 1) -> None:
            return None

        def observe(self, _value: float | int) -> None:
            return None

        def set(self, _value: float | int) -> None:
            return None

    def Counter(*_args: object, **_kwargs: object) -> _NoopMetric:  # type: ignore[no-redef]
        return _NoopMetric()

    def Gauge(*_args: object, **_kwargs: object) -> _NoopMetric:  # type: ignore[no-redef]
        return _NoopMetric()

    def Histogram(*_args: object, **_kwargs: object) -> _NoopMetric:  # type: ignore[no-redef]
        return _NoopMetric()

from polybot.backtesting.results import BacktestResult
from polybot.live_readiness.readiness_score import LiveReadinessReport
from polybot.paper_trading.models import PaperTradingResult
from polybot.research.signals import ResearchSignal
from polybot.shadow_trading.models import ShadowTradingResult

collector_runs_total = Counter(
    "polybot_collector_runs_total",
    "Collector runs by job type and status.",
    ["job_type", "status"],
)
collector_rows_seen_total = Counter(
    "polybot_collector_rows_seen_total",
    "Rows seen by collectors.",
    ["job_type"],
)
collector_rows_written_total = Counter(
    "polybot_collector_rows_written_total",
    "Rows written by collectors.",
    ["job_type"],
)
collector_duration_seconds = Histogram(
    "polybot_collector_duration_seconds",
    "Collector run duration in seconds.",
    ["job_type"],
)
stale_snapshots_total = Counter(
    "polybot_stale_snapshots_total",
    "Detected stale orderbook snapshots.",
    ["job_type"],
)

paper_trading_runs_total = Counter(
    "polybot_paper_trading_runs_total",
    "Paper trading runs by strategy.",
    ["strategy", "status"],
)
paper_trading_fills_total = Counter(
    "polybot_paper_trading_fills_total",
    "Paper trading fills by strategy.",
    ["strategy"],
)
paper_trading_rejected_orders_total = Counter(
    "polybot_paper_trading_rejected_orders_total",
    "Paper trading rejected orders by strategy.",
    ["strategy"],
)
paper_trading_fill_rate = Gauge(
    "polybot_paper_trading_fill_rate",
    "Latest paper trading fill rate by strategy.",
    ["strategy"],
)
paper_trading_net_pnl = Gauge(
    "polybot_paper_trading_net_pnl",
    "Latest paper trading net PnL by strategy.",
    ["strategy"],
)

research_signals_total = Counter(
    "polybot_research_signals_total",
    "Research signals by type and severity.",
    ["signal_type", "severity"],
)

backtests_total = Counter(
    "polybot_backtests_total",
    "Backtest runs by strategy and status.",
    ["strategy", "status"],
)
backtest_net_pnl = Gauge(
    "polybot_backtest_net_pnl",
    "Latest backtest net PnL by strategy.",
    ["strategy"],
)
shadow_trading_runs_total = Counter(
    "polybot_shadow_trading_runs_total",
    "Shadow trading runs by strategy and status.",
    ["strategy", "status"],
)
shadow_trading_impossible_fills_total = Counter(
    "polybot_shadow_trading_impossible_fills_total",
    "Impossible shadow fills by strategy.",
    ["strategy"],
)
shadow_trading_average_slippage = Gauge(
    "polybot_shadow_trading_average_slippage",
    "Latest shadow average slippage by strategy.",
    ["strategy"],
)
shadow_trading_fill_probability = Gauge(
    "polybot_shadow_trading_fill_probability",
    "Latest shadow fill probability by strategy.",
    ["strategy"],
)
live_readiness_score = Gauge(
    "polybot_live_readiness_score",
    "Latest live readiness score.",
)
live_readiness_checks_total = Counter(
    "polybot_live_readiness_checks_total",
    "Live readiness checks by status and severity.",
    ["status", "severity"],
)


def record_collector_run(
    *,
    job_type: str,
    status: str,
    rows_seen: int,
    rows_written: int,
    started_at: datetime,
    finished_at: datetime,
) -> None:
    collector_runs_total.labels(job_type=job_type, status=status).inc()
    collector_rows_seen_total.labels(job_type=job_type).inc(rows_seen)
    collector_rows_written_total.labels(job_type=job_type).inc(rows_written)
    collector_duration_seconds.labels(job_type=job_type).observe(
        max((finished_at - started_at).total_seconds(), 0)
    )


def record_stale_snapshots(*, job_type: str, count: int) -> None:
    if count > 0:
        stale_snapshots_total.labels(job_type=job_type).inc(count)


def record_paper_trading_result(result: PaperTradingResult, *, status: str = "success") -> None:
    paper_trading_runs_total.labels(strategy=result.strategy_name, status=status).inc()
    paper_trading_fills_total.labels(strategy=result.strategy_name).inc(result.filled_orders)
    paper_trading_rejected_orders_total.labels(strategy=result.strategy_name).inc(
        result.rejected_orders
    )
    paper_trading_fill_rate.labels(strategy=result.strategy_name).set(float(result.fill_rate))
    paper_trading_net_pnl.labels(strategy=result.strategy_name).set(float(result.net_pnl))
    record_signal_count(result.signals)


def record_signal_count(signals: list[ResearchSignal]) -> None:
    for signal in signals:
        research_signals_total.labels(
            signal_type=signal.signal_type,
            severity=signal.severity,
        ).inc()


def record_backtest_result(result: BacktestResult, *, status: str = "success") -> None:
    backtests_total.labels(strategy=result.strategy_id, status=status).inc()
    backtest_net_pnl.labels(strategy=result.strategy_id).set(float(result.net_pnl))


def record_shadow_trading_result(result: ShadowTradingResult) -> None:
    shadow_trading_runs_total.labels(strategy=result.strategy_name, status=result.status).inc()
    shadow_trading_impossible_fills_total.labels(strategy=result.strategy_name).inc(
        result.impossible_fill_count
    )
    shadow_trading_average_slippage.labels(strategy=result.strategy_name).set(
        float(result.average_slippage)
    )
    shadow_trading_fill_probability.labels(strategy=result.strategy_name).set(
        float(result.fill_probability)
    )


def record_live_readiness_report(report: LiveReadinessReport) -> None:
    live_readiness_score.set(float(report.live_readiness_score))
    for check in report.checks:
        live_readiness_checks_total.labels(
            status="passed" if check.passed else "failed",
            severity=check.severity,
        ).inc()
