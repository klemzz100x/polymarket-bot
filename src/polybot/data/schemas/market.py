from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Outcome(BaseModel):
    model_config = ConfigDict(frozen=True)

    market_id: str
    condition_id: str | None = None
    outcome_index: int
    name: str
    asset_id: str | None = None
    price: Decimal | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class MarketMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    market_id: str
    condition_id: str | None = None
    slug: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    event_slug: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    game_start_time: datetime | None = None
    description: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class Market(BaseModel):
    model_config = ConfigDict(frozen=True)

    market_id: str
    condition_id: str | None = None
    question: str
    slug: str | None = None
    active: bool = False
    closed: bool = False
    archived: bool = False
    accepting_orders: bool | None = None
    enable_order_book: bool | None = None
    category: str | None = None
    volume: Decimal | None = None
    liquidity: Decimal | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    outcomes: list[Outcome] = Field(default_factory=list)
    metadata: MarketMetadata | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)

