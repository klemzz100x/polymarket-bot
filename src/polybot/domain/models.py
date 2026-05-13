from dataclasses import dataclass, field
from datetime import datetime
from polybot.core.compat import UTC
from polybot.core.compat import StrEnum


class NoteStatus(StrEnum):
    TO_SUMMARIZE = "to_summarize"
    TO_TEST = "to_test"
    INTEGRATED = "integrated"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class TwitterThreadSource:
    url: str
    author: str | None
    status_id: str | None
    raw_text: str = ""
    discovered_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def note_title(self) -> str:
        if self.author and self.status_id:
            return f"Twitter Thread - {self.author} - {self.status_id}"
        return "Twitter Thread - Unknown"


@dataclass(frozen=True, slots=True)
class AgentRepo:
    url: str
    owner: str
    name: str
    discovered_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def local_dir_name(self) -> str:
        return f"{self.owner}__{self.name}"


@dataclass(frozen=True, slots=True)
class CloneResult:
    repo: AgentRepo
    path: str
    status: str
    message: str = ""

