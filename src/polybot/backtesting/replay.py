from collections.abc import Iterator
from dataclasses import dataclass

from polybot.data.schemas import OrderBookSnapshot


@dataclass(frozen=True, slots=True)
class ReplayEvent:
    sequence: int
    snapshot: OrderBookSnapshot


class MarketReplay:
    def __init__(self, snapshots: list[OrderBookSnapshot]) -> None:
        self.snapshots = sorted(snapshots, key=lambda snapshot: snapshot.snapshot_ts)

    def __iter__(self) -> Iterator[ReplayEvent]:
        for index, snapshot in enumerate(self.snapshots):
            yield ReplayEvent(sequence=index, snapshot=snapshot)

