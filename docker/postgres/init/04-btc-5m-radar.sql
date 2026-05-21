CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.btc_5m_monitor_ticks (
    id BIGSERIAL PRIMARY KEY,
    observed_at TIMESTAMPTZ NOT NULL,
    condition_id TEXT NOT NULL,
    market_slug TEXT NOT NULL,
    market_title TEXT NOT NULL,
    market_start TIMESTAMPTZ,
    market_end TIMESTAMPTZ,
    up_asset_id TEXT NOT NULL,
    down_asset_id TEXT NOT NULL,
    binance_price NUMERIC(38, 18) NOT NULL,
    binance_change_30s_pct NUMERIC(38, 18) NOT NULL DEFAULT 0,
    up_bid NUMERIC(38, 18),
    up_ask NUMERIC(38, 18),
    down_bid NUMERIC(38, 18),
    down_ask NUMERIC(38, 18),
    pair_cost NUMERIC(38, 18),
    spread NUMERIC(38, 18) NOT NULL DEFAULT 0,
    market_state TEXT NOT NULL,
    rejected_reason TEXT NOT NULL DEFAULT '',
    latency_signal JSONB,
    pair_arb_signal JSONB,
    has_latency_signal BOOLEAN NOT NULL DEFAULT false,
    has_pair_arb_signal BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_btc_5m_monitor_ticks_observed
    ON app.btc_5m_monitor_ticks(observed_at DESC);

CREATE INDEX IF NOT EXISTS ix_btc_5m_monitor_ticks_market_observed
    ON app.btc_5m_monitor_ticks(condition_id, observed_at DESC);

CREATE INDEX IF NOT EXISTS ix_btc_5m_monitor_ticks_state_observed
    ON app.btc_5m_monitor_ticks(market_state, observed_at DESC);
