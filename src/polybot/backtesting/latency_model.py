from datetime import datetime, timedelta


class LatencyModel:
    def __init__(self, latency_ms: int = 500) -> None:
        self.latency_ms = latency_ms

    def effective_time(self, created_at: datetime) -> datetime:
        return created_at + timedelta(milliseconds=self.latency_ms)

