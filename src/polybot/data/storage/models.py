import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class MarketORM(Base):
    __tablename__ = "markets"
    __table_args__ = (
        UniqueConstraint("condition_id", name="uq_markets_condition_id"),
        UniqueConstraint("slug", name="uq_markets_slug"),
        {"schema": "app"},
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    condition_id: Mapped[str | None] = mapped_column(String, nullable=True)
    question: Mapped[str] = mapped_column(Text)
    slug: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    closed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    accepting_orders: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    enable_order_book: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    volume: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    liquidity: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    outcomes: Mapped[list["MarketOutcomeORM"]] = relationship(
        back_populates="market", cascade="all, delete-orphan"
    )


class MarketOutcomeORM(Base):
    __tablename__ = "market_outcomes"
    __table_args__ = (
        UniqueConstraint("market_id", "outcome_index", name="uq_market_outcome_index"),
        UniqueConstraint("asset_id", name="uq_market_outcome_asset_id"),
        Index("ix_market_outcomes_condition_id", "condition_id"),
        {"schema": "app"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[str] = mapped_column(ForeignKey("app.markets.id", ondelete="CASCADE"))
    condition_id: Mapped[str | None] = mapped_column(String, nullable=True)
    outcome_index: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String)
    asset_id: Mapped[str | None] = mapped_column(String, nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    market: Mapped[MarketORM] = relationship(back_populates="outcomes")


class OrderBookSnapshotORM(Base):
    __tablename__ = "orderbook_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "asset_id", "snapshot_ts", "book_hash", name="uq_orderbook_asset_ts_hash"
        ),
        Index("ix_orderbook_snapshots_condition_ts", "condition_id", "snapshot_ts"),
        Index("ix_orderbook_snapshots_asset_ts", "asset_id", "snapshot_ts"),
        {"schema": "app"},
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    condition_id: Mapped[str] = mapped_column(String, index=True)
    asset_id: Mapped[str] = mapped_column(String, index=True)
    snapshot_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    book_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    min_order_size: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    tick_size: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    neg_risk: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_trade_price: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    levels: Mapped[list["OrderBookLevelORM"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class OrderBookLevelORM(Base):
    __tablename__ = "orderbook_levels"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "side", "level_index", name="uq_orderbook_level"),
        Index("ix_orderbook_levels_price", "price"),
        {"schema": "app"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("app.orderbook_snapshots.id", ondelete="CASCADE"), index=True
    )
    side: Mapped[str] = mapped_column(String(8), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(38, 18))
    size: Mapped[Decimal] = mapped_column(Numeric(38, 18))
    level_index: Mapped[int] = mapped_column(Integer)

    snapshot: Mapped[OrderBookSnapshotORM] = relationship(back_populates="levels")


class TradeORM(Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index("ix_trades_condition_ts", "condition_id", "traded_at"),
        Index("ix_trades_asset_ts", "asset_id", "traded_at"),
        Index("ix_trades_transaction_hash", "transaction_hash"),
        {"schema": "app"},
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    condition_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    asset_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    side: Mapped[str | None] = mapped_column(String, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(38, 18))
    size: Mapped[Decimal] = mapped_column(Numeric(38, 18))
    traded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    outcome: Mapped[str | None] = mapped_column(String, nullable=True)
    outcome_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transaction_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    proxy_wallet: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PriceTickORM(Base):
    __tablename__ = "price_ticks"
    __table_args__ = (
        UniqueConstraint("asset_id", "ts", "source", name="uq_price_tick_asset_ts_source"),
        Index("ix_price_ticks_asset_ts", "asset_id", "ts"),
        {"schema": "app"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[str] = mapped_column(String, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(38, 18))
    source: Mapped[str] = mapped_column(String, default="clob_prices_history")
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DataIngestionLogORM(Base):
    __tablename__ = "ingestion_logs"
    __table_args__ = (
        Index("ix_ingestion_logs_source_started", "source", "started_at"),
        {"schema": "app"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String, index=True)
    job_type: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rows_seen: Mapped[int] = mapped_column(Integer, default=0)
    rows_written: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict)


class RawApiPayloadORM(Base):
    __tablename__ = "raw_api_payloads"
    __table_args__ = (
        UniqueConstraint("source", "endpoint", "external_id", name="uq_raw_api_payload_external"),
        Index("ix_raw_api_payloads_collected", "source", "collected_at"),
        {"schema": "app"},
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String, index=True)
    endpoint: Mapped[str] = mapped_column(String, index=True)
    external_id: Mapped[str | None] = mapped_column(String, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    payload: Mapped[dict[str, object]] = mapped_column(JSON)

