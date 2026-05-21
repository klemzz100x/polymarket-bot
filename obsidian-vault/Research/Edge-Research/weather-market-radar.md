---
type: "weather-market-radar"
tags: ["research", "weather", "edge", "paper-only"]
---
# Weather Market Radar

Generated at: `2026-05-13T14:19:34.447897+00:00`

Scan ID: `weather-20260513-141933-ef623dfe`

Mode: `research_read_only`. No live trading, no order placement, no private key usage.

## Verdict
- Best thread-derived edge: weather markets are not HFT first; they are objective external-data markets where forecast/advisory updates can lead Polymarket repricing.
- Promotion rule: do not treat a market as tradable until its resolution source, external forecast feed, spread, and depth are mapped.
- Next build step: add forecast snapshots for `daily_temperature` and NHC advisory timestamps for `hurricane_storm`.

## State Counts
- FORECAST_WATCH: 14
- NO_BOOK: 26

## Family Counts
- daily_temperature: 40

## Top Markets
| State | Spread | Family | Market | Location | Hypothesis |
|---|---:|---|---|---|---|
| FORECAST_WATCH | 0.0010 | daily_temperature | Will 2026 rank as the sixth-hottest year on record or lower? |  | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| FORECAST_WATCH | 0.0010 | daily_temperature | Will 2026 be the fourth-hottest year on record? |  | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| FORECAST_WATCH | 0.0020 | daily_temperature | Will 2026 be the fifth-hottest year on record? |  | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| FORECAST_WATCH | 0.0020 | daily_temperature | Will 2026 be the third-hottest year on record? |  | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| FORECAST_WATCH | 0.0020 | daily_temperature | Will May 2026 be the 3rd hottest on record? |  | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| FORECAST_WATCH | 0.0030 | daily_temperature | Will the highest temperature in Austin be 78°F or higher on May 13? | Austin | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| FORECAST_WATCH | 0.0050 | daily_temperature | Will the highest temperature in Seattle be 72°F or higher on May 13? | Seattle | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| FORECAST_WATCH | 0.0070 | daily_temperature | Will the highest temperature in Paris be 14°C on May 13? | Paris | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| FORECAST_WATCH | 0.0080 | daily_temperature | Will the highest temperature in London be 15°C on May 13? | London | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| FORECAST_WATCH | 0.0090 | daily_temperature | Will May 2026 be the 4th or lower hottest on record? |  | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| FORECAST_WATCH | 0.0100 | daily_temperature | Will 2026 be the hottest year on record? |  | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| FORECAST_WATCH | 0.0100 | daily_temperature | Will 2026 be the second-hottest year on record? |  | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| FORECAST_WATCH | 0.0100 | daily_temperature | Will any month of 2026 be the hottest on record? |  | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| FORECAST_WATCH | 0.0200 | daily_temperature | Will the highest temperature in London be 13°C on May 13? | London | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| NO_BOOK | n/a | daily_temperature | Will the highest temperature in Hong Kong be 31°C or higher on May 13? | Hong Kong | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| NO_BOOK | n/a | daily_temperature | Will the highest temperature in Hong Kong be 30°C on May 13? | Hong Kong | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| NO_BOOK | n/a | daily_temperature | Will the highest temperature in Seoul be 20°C on May 13? | Seoul | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| NO_BOOK | n/a | daily_temperature | Will the highest temperature in Seoul be 23°C or higher on May 13? | Seoul | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| NO_BOOK | n/a | daily_temperature | Will the highest temperature in Hong Kong be 29°C on May 13? | Hong Kong | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
| NO_BOOK | n/a | daily_temperature | Will the highest temperature in Shanghai be 27°C on May 13? | Shanghai | Replay official forecast updates vs market mid; edge only if forecast-implied bucket diver |
