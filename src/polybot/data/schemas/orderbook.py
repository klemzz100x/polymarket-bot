from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrderBookSide(StrEnum):
    BID = "bid"
    ASK = "ask"


class OrderBookLevel(BaseModel):
    model_config = ConfigDict(frozen=True)

    side: OrderBookSide
    price: Decimal
    size: Decimal
    level_index: int


class OrderBookSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    condition_id: str
    asset_id: str
    snapshot_ts: datetime
    received_at: datetime
    book_hash: str | None = None
    min_order_size: Decimal | None = None
    tick_size: Decimal | None = None
    neg_risk: bool | None = None
    last_trade_price: Decimal | None = None
    bids: list[OrderBookLevel] = Field(default_factory=list)
    asks: list[OrderBookLevel] = Field(default_factory=list)
    raw_payload: dict[str, Any] = Field(default_factory=dict)

    @property
    def best_bid(self) -> Decimal | None:
        return self.bids[0].price if self.bids else None

    @property
    def best_ask(self) -> Decimal | None:
        return self.asks[0].price if self.asks else None

    @property
    def spread(self) -> Decimal | None:
        if self.best_bid is None or self.best_ask is None:
            return None
        return self.best_ask - self.best_bid

