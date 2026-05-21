CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.weather_market_radar_ticks (
    id BIGSERIAL PRIMARY KEY,
    scan_id TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    event_id TEXT,
    event_slug TEXT,
    event_title TEXT,
    market_id TEXT,
    condition_id TEXT,
    market_slug TEXT,
    question TEXT NOT NULL,
    weather_family TEXT NOT NULL,
    location_hint TEXT,
    threshold_hint TEXT,
    end_date TIMESTAMPTZ,
    volume NUMERIC(38, 18),
    liquidity NUMERIC(38, 18),
    token_count INTEGER NOT NULL DEFAULT 0,
    best_yes_bid NUMERIC(38, 18),
    best_yes_ask NUMERIC(38, 18),
    best_no_bid NUMERIC(38, 18),
    best_no_ask NUMERIC(38, 18),
    pair_cost NUMERIC(38, 18),
    spread NUMERIC(38, 18),
    market_state TEXT NOT NULL,
    rejected_reason TEXT NOT NULL DEFAULT '',
    edge_hypothesis TEXT NOT NULL DEFAULT '',
    source_url TEXT NOT NULL DEFAULT '',
    raw JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_weather_radar_observed
    ON app.weather_market_radar_ticks(observed_at DESC);
CREATE INDEX IF NOT EXISTS ix_weather_radar_scan
    ON app.weather_market_radar_ticks(scan_id);
CREATE INDEX IF NOT EXISTS ix_weather_radar_state_observed
    ON app.weather_market_radar_ticks(market_state, observed_at DESC);
CREATE INDEX IF NOT EXISTS ix_weather_radar_condition_observed
    ON app.weather_market_radar_ticks(condition_id, observed_at DESC);
