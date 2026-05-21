CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.weather_station_observations (
    id BIGSERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    station_id TEXT NOT NULL,
    station_name TEXT,
    report_time TIMESTAMPTZ,
    obs_time TIMESTAMPTZ,
    temp_c NUMERIC(10, 4),
    dewpoint_c NUMERIC(10, 4),
    wind_dir INTEGER,
    wind_speed INTEGER,
    source_name TEXT NOT NULL DEFAULT 'aviationweather.gov-metar',
    source_url TEXT NOT NULL DEFAULT '',
    raw_metar TEXT NOT NULL DEFAULT '',
    raw JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (station_id, report_time, raw_metar)
);

CREATE INDEX IF NOT EXISTS ix_weather_station_observations_collected
    ON app.weather_station_observations(collected_at DESC);

CREATE INDEX IF NOT EXISTS ix_weather_station_observations_station_report
    ON app.weather_station_observations(station_id, report_time DESC);
