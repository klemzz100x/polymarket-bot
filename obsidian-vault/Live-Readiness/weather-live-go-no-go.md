---
type: "weather-live-go-no-go"
tags: ["live-readiness", "weather", "safety"]
---
# Weather Live Go/No-Go

Generated at: `2026-05-13T14:21:54.633670+00:00`

Status: `NO_GO`

Score: `0.8889`

## Checks
| Status | Check | Value | Required | Blocker |
|---|---|---|---|---|
| PASS | live_trading_still_disabled | false | false during readiness | True |
| PASS | live_execution_mode_disabled | DISABLED | DISABLED during readiness | True |
| PASS | no_private_key_loaded_in_readiness | empty | empty until explicit live cutover | True |
| PASS | weather_scan_sample_size_24h | 12 | >= 12 | True |
| FAIL | edge_stability_window | 0.80h | >= 6h | True |
| PASS | exact_station_proxy_edge_candidates | 7 | >= 1 | True |
| PASS | hko_source_adapter | 0 | 0 unresolved HKO candidates | False |
| PASS | fresh_station_observations | 3 | >= 1 station with temp in last 2h | True |
| PASS | generic_live_readiness_report | ready 100.000000000000000000 | ready/pass and score >= 0.80 | True |

## Blockers
- edge_stability_window: value 0.80h, required >= 6h

## Recommendations
- Keep LIVE_TRADING_ENABLED=false and LIVE_EXECUTION_MODE=DISABLED.
- Do not paste or store seed phrases in chat, repo, dashboard, or .env.
- Use a fresh dedicated Polymarket wallet with tiny capital only.
- Keep first live cutover at micro-size and maker/limit-only until fill behavior is observed.
- Before changing env flags, run this gate again and archive the report.
