from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DataIngestionLog(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    job_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    rows_seen: int = 0
    rows_written: int = 0
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

