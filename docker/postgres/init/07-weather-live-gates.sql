CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.weather_live_gate_reports (
    id BIGSERIAL PRIMARY KEY,
    report_id TEXT NOT NULL UNIQUE,
    generated_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    score NUMERIC(10, 4) NOT NULL,
    checks JSONB NOT NULL,
    blockers JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_weather_live_gate_reports_generated
    ON app.weather_live_gate_reports(generated_at DESC);
CREATE INDEX IF NOT EXISTS ix_weather_live_gate_reports_status
    ON app.weather_live_gate_reports(status, generated_at DESC);
