CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.weather_forecast_edges (
    id BIGSERIAL PRIMARY KEY,
    scan_id TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    radar_tick_id BIGINT REFERENCES app.weather_market_radar_ticks(id) ON DELETE SET NULL,
    condition_id TEXT,
    question TEXT NOT NULL,
    location_hint TEXT NOT NULL,
    target_date DATE,
    threshold_hint TEXT,
    forecast_max_c NUMERIC(18, 8),
    model_sigma_c NUMERIC(18, 8),
    fair_yes NUMERIC(18, 8),
    market_mid NUMERIC(18, 8),
    best_yes_bid NUMERIC(18, 8),
    best_yes_ask NUMERIC(18, 8),
    best_no_ask NUMERIC(18, 8),
    spread NUMERIC(18, 8),
    edge_yes NUMERIC(18, 8),
    edge_no NUMERIC(18, 8),
    action_bias TEXT NOT NULL,
    model_state TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    source_name TEXT NOT NULL DEFAULT 'open-meteo-proxy',
    source_url TEXT NOT NULL DEFAULT '',
    raw JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_weather_forecast_edges_observed
    ON app.weather_forecast_edges(observed_at DESC);
CREATE INDEX IF NOT EXISTS ix_weather_forecast_edges_state_observed
    ON app.weather_forecast_edges(model_state, observed_at DESC);
CREATE INDEX IF NOT EXISTS ix_weather_forecast_edges_scan
    ON app.weather_forecast_edges(scan_id);
