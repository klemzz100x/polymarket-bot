# Grafana Monitoring

This folder contains local Grafana provisioning for the research-only Polymarket stack.

Dashboards focus on:
- ingestion health
- paper trading activity
- fill quality
- shadow trading activity
- live readiness
- signal activity
- stale markets
- DB row growth
- cache freshness

Start with:

```bash
docker compose --profile observability up -d prometheus grafana
```

Grafana reads dashboards from `monitoring/grafana/dashboards` and the Prometheus datasource from `monitoring/grafana/provisioning`.
