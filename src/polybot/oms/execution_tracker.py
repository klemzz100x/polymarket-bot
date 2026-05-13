from dataclasses import dataclass, field

from polybot.live_execution.models import ExecutionReport


@dataclass(slots=True)
class ExecutionTracker:
    reports: list[ExecutionReport] = field(default_factory=list)

    def record(self, report: ExecutionReport) -> None:
        self.reports.append(report)

    def rejected_count(self) -> int:
        return sum(1 for report in self.reports if not report.accepted)

    def accepted_count(self) -> int:
        return sum(1 for report in self.reports if report.accepted)
