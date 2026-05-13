from pathlib import Path

from polybot.paper_trading.models import PaperTradingEvent


class JsonlPaperLedger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: PaperTradingEvent) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(event.to_json() + "\n")

    def append_many(self, events: list[PaperTradingEvent]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(event.to_json() + "\n")

