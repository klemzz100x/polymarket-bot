CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.markets (
    id TEXT PRIMARY KEY,
    condition_id TEXT UNIQUE,
    question TEXT NOT NULL,
    slug TEXT UNIQUE,
    active BOOLEAN NOT NULL DEFAULT FALSE,
    closed BOOLEAN NOT NULL DEFAULT FALSE,
    archived BOOLEAN NOT NULL DEFAULT FALSE,
    accepting_orders BOOLEAN,
    enable_order_book BOOLEAN,
    category TEXT,
    volume NUMERIC(38, 18),
    liquidity NUMERIC(38, 18),
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    source_created_at TIMESTAMPTZ,
    source_updated_at TIMESTAMPTZ,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.market_outcomes (
    id BIGSERIAL PRIMARY KEY,
    market_id TEXT NOT NULL REFERENCES app.markets(id) ON DELETE CASCADE,
    condition_id TEXT,
    outcome_index INTEGER NOT NULL,
    name TEXT NOT NULL,
    asset_id TEXT UNIQUE,
    price NUMERIC(38, 18),
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_market_outcome_index UNIQUE (market_id, outcome_index)
);

CREATE TABLE IF NOT EXISTS app.orderbook_snapshots (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    condition_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    snapshot_ts TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    book_hash TEXT,
    min_order_size NUMERIC(38, 18),
    tick_size NUMERIC(38, 18),
    neg_risk BOOLEAN,
    last_trade_price NUMERIC(38, 18),
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_orderbook_asset_ts_hash UNIQUE (asset_id, snapshot_ts, book_hash)
);

CREATE TABLE IF NOT EXISTS app.orderbook_levels (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id TEXT NOT NULL REFERENCES app.orderbook_snapshots(id) ON DELETE CASCADE,
    side TEXT NOT NULL CHECK (side IN ('bid', 'ask')),
    price NUMERIC(38, 18) NOT NULL,
    size NUMERIC(38, 18) NOT NULL,
    level_index INTEGER NOT NULL,
    CONSTRAINT uq_orderbook_level UNIQUE (snapshot_id, side, level_index)
);

CREATE TABLE IF NOT EXISTS app.trades (
    id TEXT PRIMARY KEY,
    condition_id TEXT,
    asset_id TEXT,
    side TEXT,
    price NUMERIC(38, 18) NOT NULL,
    size NUMERIC(38, 18) NOT NULL,
    traded_at TIMESTAMPTZ NOT NULL,
    outcome TEXT,
    outcome_index INTEGER,
    transaction_hash TEXT,
    proxy_wallet TEXT,
    title TEXT,
    slug TEXT,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.price_ticks (
    id BIGSERIAL PRIMARY KEY,
    asset_id TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    price NUMERIC(38, 18) NOT NULL,
    source TEXT NOT NULL DEFAULT 'clob_prices_history',
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_price_tick_asset_ts_source UNIQUE (asset_id, ts, source)
);

CREATE TABLE IF NOT EXISTS app.ingestion_logs (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    rows_seen INTEGER NOT NULL DEFAULT 0,
    rows_written INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS app.raw_api_payloads (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    source TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    external_id TEXT,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload JSONB NOT NULL,
    CONSTRAINT uq_raw_api_payload_external UNIQUE (source, endpoint, external_id)
);

CREATE INDEX IF NOT EXISTS ix_markets_active_closed ON app.markets(active, closed);
CREATE INDEX IF NOT EXISTS ix_markets_category ON app.markets(category);
CREATE INDEX IF NOT EXISTS ix_market_outcomes_condition_id ON app.market_outcomes(condition_id);
CREATE INDEX IF NOT EXISTS ix_orderbook_snapshots_condition_ts ON app.orderbook_snapshots(condition_id, snapshot_ts);
CREATE INDEX IF NOT EXISTS ix_orderbook_snapshots_asset_ts ON app.orderbook_snapshots(asset_id, snapshot_ts);
CREATE INDEX IF NOT EXISTS ix_orderbook_levels_price ON app.orderbook_levels(price);
CREATE INDEX IF NOT EXISTS ix_trades_condition_ts ON app.trades(condition_id, traded_at);
CREATE INDEX IF NOT EXISTS ix_trades_asset_ts ON app.trades(asset_id, traded_at);
CREATE INDEX IF NOT EXISTS ix_trades_transaction_hash ON app.trades(transaction_hash);
CREATE INDEX IF NOT EXISTS ix_price_ticks_asset_ts ON app.price_ticks(asset_id, ts);
CREATE INDEX IF NOT EXISTS ix_ingestion_logs_source_started ON app.ingestion_logs(source, started_at);
CREATE INDEX IF NOT EXISTS ix_raw_api_payloads_collected ON app.raw_api_payloads(source, collected_at);
