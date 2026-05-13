CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.paper_trading_runs (
    id TEXT PRIMARY KEY,
    market_id TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    decision_mode TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    snapshot_count INTEGER NOT NULL DEFAULT 0,
    signal_count INTEGER NOT NULL DEFAULT 0,
    attempted_orders INTEGER NOT NULL DEFAULT 0,
    filled_orders INTEGER NOT NULL DEFAULT 0,
    rejected_orders INTEGER NOT NULL DEFAULT 0,
    final_cash NUMERIC(38, 18) NOT NULL DEFAULT 0,
    final_equity NUMERIC(38, 18) NOT NULL DEFAULT 0,
    net_pnl NUMERIC(38, 18) NOT NULL DEFAULT 0,
    fees NUMERIC(38, 18) NOT NULL DEFAULT 0,
    result JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.paper_trading_events (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES app.paper_trading_runs(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_ts TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.paper_equity_snapshots (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES app.paper_trading_runs(id) ON DELETE CASCADE,
    market_id TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    snapshot_ts TIMESTAMPTZ NOT NULL,
    equity NUMERIC(38, 18) NOT NULL DEFAULT 0,
    cash NUMERIC(38, 18) NOT NULL DEFAULT 0,
    net_pnl NUMERIC(38, 18) NOT NULL DEFAULT 0,
    exposure NUMERIC(38, 18) NOT NULL DEFAULT 0,
    positions JSONB NOT NULL DEFAULT '{}'::jsonb,
    source TEXT NOT NULL DEFAULT 'paper_trading',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_paper_equity_run_ts_source UNIQUE (run_id, snapshot_ts, source)
);

CREATE INDEX IF NOT EXISTS ix_paper_trading_runs_market_started
    ON app.paper_trading_runs(market_id, started_at);

CREATE INDEX IF NOT EXISTS ix_paper_trading_events_run_ts
    ON app.paper_trading_events(run_id, event_ts);

CREATE INDEX IF NOT EXISTS ix_paper_equity_snapshots_strategy_ts
    ON app.paper_equity_snapshots(strategy_name, snapshot_ts);

CREATE INDEX IF NOT EXISTS ix_paper_equity_snapshots_market_ts
    ON app.paper_equity_snapshots(market_id, snapshot_ts);

CREATE TABLE IF NOT EXISTS app.shadow_trading_runs (
    id TEXT PRIMARY KEY,
    market_id TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    snapshot_count INTEGER NOT NULL DEFAULT 0,
    signal_count INTEGER NOT NULL DEFAULT 0,
    decision_count INTEGER NOT NULL DEFAULT 0,
    theoretical_fill_count INTEGER NOT NULL DEFAULT 0,
    missed_fill_count INTEGER NOT NULL DEFAULT 0,
    impossible_fill_count INTEGER NOT NULL DEFAULT 0,
    average_slippage NUMERIC(38, 18) NOT NULL DEFAULT 0,
    average_delay_ms NUMERIC(38, 18) NOT NULL DEFAULT 0,
    fill_probability NUMERIC(38, 18) NOT NULL DEFAULT 0,
    result JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.shadow_trading_decisions (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES app.shadow_trading_runs(id) ON DELETE CASCADE,
    decision_id TEXT NOT NULL UNIQUE,
    decision_ts TIMESTAMPTZ NOT NULL,
    market_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    signal_type TEXT,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    order_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    fill_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    comparison_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.live_readiness_reports (
    id TEXT PRIMARY KEY,
    generated_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    live_readiness_score NUMERIC(38, 18) NOT NULL DEFAULT 0,
    execution_quality_score NUMERIC(38, 18) NOT NULL DEFAULT 0,
    infrastructure_health_score NUMERIC(38, 18) NOT NULL DEFAULT 0,
    strategy_stability_score NUMERIC(38, 18) NOT NULL DEFAULT 0,
    kill_switch_state TEXT NOT NULL,
    report JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.kill_switch_events (
    id BIGSERIAL PRIMARY KEY,
    event_ts TIMESTAMPTZ NOT NULL,
    state TEXT NOT NULL,
    trigger TEXT NOT NULL,
    severity TEXT NOT NULL,
    reason TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_shadow_trading_runs_market_started
    ON app.shadow_trading_runs(market_id, started_at);

CREATE INDEX IF NOT EXISTS ix_shadow_trading_decisions_run_ts
    ON app.shadow_trading_decisions(run_id, decision_ts);

CREATE INDEX IF NOT EXISTS ix_live_readiness_reports_generated
    ON app.live_readiness_reports(generated_at);

CREATE INDEX IF NOT EXISTS ix_kill_switch_events_ts
    ON app.kill_switch_events(event_ts);

CREATE TABLE IF NOT EXISTS app.wallet_snapshots (
    id BIGSERIAL PRIMARY KEY,
    wallet_address TEXT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    total_exposure_usd NUMERIC(38, 18) NOT NULL DEFAULT 0,
    balances JSONB NOT NULL DEFAULT '[]'::jsonb,
    positions JSONB NOT NULL DEFAULT '[]'::jsonb,
    open_orders JSONB NOT NULL DEFAULT '[]'::jsonb,
    snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.live_orders (
    client_order_id TEXT PRIMARY KEY,
    exchange_order_id TEXT,
    market_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    side TEXT NOT NULL,
    price NUMERIC(38, 18) NOT NULL,
    size NUMERIC(38, 18) NOT NULL,
    notional_usd NUMERIC(38, 18) NOT NULL,
    mode TEXT NOT NULL DEFAULT 'DISABLED',
    state TEXT NOT NULL DEFAULT 'pending',
    rejection_reason TEXT NOT NULL DEFAULT '',
    order_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.live_execution_reports (
    id BIGSERIAL PRIMARY KEY,
    client_order_id TEXT NOT NULL,
    exchange_order_id TEXT,
    status TEXT NOT NULL,
    accepted BOOLEAN NOT NULL DEFAULT false,
    reason TEXT NOT NULL DEFAULT '',
    report JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.live_fills (
    fill_id TEXT PRIMARY KEY,
    exchange_order_id TEXT NOT NULL,
    client_order_id TEXT NOT NULL,
    market_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    side TEXT NOT NULL,
    price NUMERIC(38, 18) NOT NULL,
    size NUMERIC(38, 18) NOT NULL,
    fee NUMERIC(38, 18) NOT NULL DEFAULT 0,
    filled_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.live_risk_events (
    id BIGSERIAL PRIMARY KEY,
    event_ts TIMESTAMPTZ NOT NULL,
    client_order_id TEXT NOT NULL,
    market_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    allowed BOOLEAN NOT NULL DEFAULT false,
    reason TEXT NOT NULL,
    checks JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.oms_reconciliation_reports (
    id BIGSERIAL PRIMARY KEY,
    generated_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    checked_orders INTEGER NOT NULL DEFAULT 0,
    exchange_open_orders INTEGER NOT NULL DEFAULT 0,
    report JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_wallet_snapshots_wallet_ts
    ON app.wallet_snapshots(wallet_address, captured_at);

CREATE INDEX IF NOT EXISTS ix_live_orders_state_updated
    ON app.live_orders(state, updated_at);

CREATE INDEX IF NOT EXISTS ix_live_orders_strategy_market
    ON app.live_orders(strategy_name, market_id);

CREATE INDEX IF NOT EXISTS ix_live_fills_order_ts
    ON app.live_fills(client_order_id, filled_at);

CREATE INDEX IF NOT EXISTS ix_live_risk_events_ts
    ON app.live_risk_events(event_ts);

CREATE INDEX IF NOT EXISTS ix_oms_reconciliation_reports_generated
    ON app.oms_reconciliation_reports(generated_at);
