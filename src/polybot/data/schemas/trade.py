from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Trade(BaseModel):
    model_config = ConfigDict(frozen=True)

    trade_id: str
    condition_id: str | None = None
    asset_id: str | None = None
    side: str | None = None
    price: Decimal
    size: Decimal
    traded_at: datetime
    outcome: str | None = None
    outcome_index: int | None = None
    transaction_hash: str | None = None
    proxy_wallet: str | None = None
    title: str | None = None
    slug: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class PriceTick(BaseModel):
    model_config = ConfigDict(frozen=True)

    asset_id: str
    ts: datetime
    price: Decimal
    source: str = "clob_prices_history"
    raw_payload: dict[str, Any] = Field(default_factory=dict)

