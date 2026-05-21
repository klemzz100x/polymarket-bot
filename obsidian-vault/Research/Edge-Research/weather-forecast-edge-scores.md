---
type: "weather-forecast-edge-scores"
tags: ["research", "weather", "edge", "paper-only"]
---
# Weather Forecast Edge Scores

Generated at: `2026-05-13T14:19:35.433140+00:00`

Mode: `research_read_only`. Source: `open-meteo-proxy`.

Important: this is a proxy model, not a production trading signal. Before live use, verify the exact Polymarket resolution source and replay forecast timestamp changes against orderbook movement.

Promotion filters:
- Minimum proxy edge: `0.08`
- Maximum spread: `0.04`

## State Counts
- EDGE_CANDIDATE: 1
- FAIR_ALIGNED: 1
- MODEL_BLOCKED: 2
- MODEL_WATCH: 1

## Top Scores
| State | Bias | Fair Yes | Mid | Edge Yes | Edge No | Forecast C | Market | Reason |
|---|---|---:|---:|---:|---:|---:|---|---|
| EDGE_CANDIDATE | NO | 0.2977 | 0.9300 | -0.6423 | 0.6223 | 12.5000 | Will the highest temperature in London be 13°C on May 13? | NO proxy edge 0.6223 >= 0.0800 |
| MODEL_WATCH | NONE | 0.0416 | 0.0070 | 0.0306 | -0.0386 | 12.5000 | Will the highest temperature in London be 15°C on May 13? | proxy divergence below promotion threshold |
| FAIR_ALIGNED | NONE | 1.0000 | 0.9975 | 0.0010 | -0.0040 | 31.2000 | Will the highest temperature in Austin be 78°F or higher on May 13? | proxy fair value close to market |
| MODEL_BLOCKED | NONE | n/a | 0.0035 | n/a | n/a | n/a | Will the highest temperature in Seattle be 72°F or higher on May 13? | geocode missing; forecast missing |
| MODEL_BLOCKED | NONE | n/a | 0.9555 | n/a | n/a | n/a | Will the highest temperature in Paris be 14°C on May 13? | geocode missing; forecast missing |
