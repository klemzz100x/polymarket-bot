---
tags: [sc-010, weather, temperature, 2026-05-21]
date: 2026-05-21
opportunities: 17
cities_scanned: 10
---

# SC-010 Weather Markets — 2026-05-21

**Villes** : 10 | **Jours** : 4 | **Opportunités** : 17
**Source forecasts** : Open-Meteo (température max journalière)

## Technique (@AlterEgo_eth)

Slug : `highest-temperature-in-{city}-on-{month}-{day}-{year}`
API : `GET gamma-api.polymarket.com/events?slug={slug}`
→ récupère tous les buckets de température avec leurs prix YES/NO
→ compare forecast Open-Meteo avec les buckets → edge si désalignement

## Opportunités

| # | Ville | Date | Signal | Prix | Edge% | Forecast | Bucket |
|---|-------|------|--------|------|-------|----------|--------|
| 1 | Seoul | 2026-05-21 | BUY_YES | 0.000 | +100.00% | 17.3°C | [17–18] |
| 2 | Tokyo | 2026-05-21 | BUY_YES | 0.000 | +100.00% | 20.5°C | [20–21] |
| 3 | Tokyo | 2026-05-21 | BUY_NO | 1.000 | +100.00% | 20.5°C | [23+] |
| 4 | Miami | 2026-05-21 | BUY_YES | 0.000 | +100.00% | 29.2°C | [-999–77] |
| 5 | Los Angeles | 2026-05-21 | BUY_YES | 0.001 | +99.95% | 29.3°C | [-999–55] |
| 6 | Miami | 2026-05-22 | BUY_YES | 0.002 | +99.85% | 29.9°C | [-999–77] |
| 7 | Los Angeles | 2026-05-22 | BUY_YES | 0.004 | +99.55% | 23.6°C | [-999–61] |
| 8 | Tokyo | 2026-05-22 | BUY_YES | 0.007 | +99.30% | 15.0°C | [14–15] |
| 9 | Seoul | 2026-05-21 | BUY_NO | 0.993 | +99.25% | 17.3°C | [20–21] |
| 10 | Chicago | 2026-05-22 | BUY_YES | 0.008 | +99.20% | 16.7°C | [-999–47] |
| 11 | Tokyo | 2026-05-22 | BUY_YES | 0.034 | +96.65% | 15.0°C | [15–16] |
| 12 | Paris | 2026-05-22 | BUY_YES | 0.140 | +86.00% | 27.8°C | [27–28] |
| 13 | Seoul | 2026-05-22 | BUY_YES | 0.215 | +78.50% | 27.1°C | [27+] |
| 14 | London | 2026-05-21 | BUY_YES | 0.380 | +62.00% | 23.2°C | [23–24] |
| 15 | London | 2026-05-22 | BUY_YES | 0.395 | +60.50% | 27.2°C | [27–28] |
| 16 | Chicago | 2026-05-21 | BUY_YES | 0.415 | +58.50% | 13.8°C | [-999–59] |
| 17 | Paris | 2026-05-21 | BUY_YES | 0.535 | +46.50% | 24.6°C | [24–25] |

## Meilleure opportunité

**[BUY_YES] Seoul 2026-05-21**
- Forecast 17.3°C falls in [17.0,18.0] bucket. Market YES only at 0.000.
- Condition ID : `0x4e8c763e241495d7b75f49be59a19bc0e3f3b1759fe3cd0276f07b97df6e8c61`

→ `tmp\weather_market_scan.json`
