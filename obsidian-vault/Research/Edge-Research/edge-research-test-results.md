---
type: "edge-research-tests"
tags: ["research", "edge", "paper-only"]
---
# Edge Research Test Results

Generated at: `2026-05-13T10:17:33.643330+00:00`

Mode: `research_readiness_only`

No live trading, no order placement, no private key usage. These tests only inspect local market metadata and stored orderbook snapshots.

## weather_event_discovery
- Status: `needs_data`
- Candidate markets: 0
- Covered markets: 0
- Snapshots: 0
- Hypothesis: Forecast updates can identify weather markets that reprice slower than external weather feeds.
- Verdict: weather_event_discovery is a valid hypothesis from the thread corpus, but local data is not dense enough yet (0/100 snapshots). Treat this as collection guidance, not a PnL signal.
- Next action: Collect weather-specific markets plus timestamped forecast snapshots before replay testing.

### Blockers
- No matching markets found in app.markets for this edge family.
- No matching markets currently have stored orderbook snapshots.
- Only 0 snapshots available; minimum for a first replay is 100.

### Sample Markets
No matching markets.

## crypto_5m_microstructure
- Status: `needs_data`
- Candidate markets: 1
- Covered markets: 0
- Snapshots: 0
- Hypothesis: CEX BTC/ETH microstructure can lead Polymarket short-window crypto markets after latency and spread.
- Verdict: crypto_5m_microstructure is a valid hypothesis from the thread corpus, but local data is not dense enough yet (0/300 snapshots). Treat this as collection guidance, not a PnL signal.
- Next action: Collect short-window crypto markets with second-level CEX reference prices and dense orderbooks.

### Blockers
- No matching markets currently have stored orderbook snapshots.
- Only 0 snapshots available; minimum for a first replay is 300.

### Sample Markets
| Snapshots | Category | Market | Condition ID |
|---:|---|---|---|
| 0 |  | Will bitcoin hit $1m before GTA VI? | `0xbb57ccf5853a85487bc3d83d04d669310d28c6c810758953b9d9b91d1aee89d2` |

## news_latency
- Status: `needs_data`
- Candidate markets: 24
- Covered markets: 0
- Snapshots: 0
- Hypothesis: Credible news events can move real-world probabilities before Polymarket fully reprices.
- Verdict: news_latency is a valid hypothesis from the thread corpus, but local data is not dense enough yet (0/100 snapshots). Treat this as collection guidance, not a PnL signal.
- Next action: Build an external event timestamp feed and map events to market condition_ids before replay.

### Blockers
- No matching markets currently have stored orderbook snapshots.
- Only 0 snapshots available; minimum for a first replay is 100.

### Sample Markets
| Snapshots | Category | Market | Condition ID |
|---:|---|---|---|
| 0 |  | Will Tim Walz win the 2028 Democratic presidential nomination? | `0x3265b10daeb30dbcc3214bd02e488551d0a5d3028392f4152e4750b943fbfc91` |
| 0 |  | Will Zohran Mamdani win the 2028 Democratic presidential nomination? | `0x3535fb2f4aef6619dde8b367cb5e5d209526bb496d5d9778428c58a0252435e3` |
| 0 |  | Will Gina Raimondo win the 2028 Democratic presidential nomination? | `0xcb239105ed21a2420ba4d85090b9bc32755c56601ffdc528afd17fd6282fe930` |
| 0 |  | Will Roy Cooper win the 2028 Democratic presidential nomination? | `0x939eeb2dea216749bd409bedde483c3f2bfb0e24d4f2d34461c0b21c6e91f010` |
| 0 |  | Will Raphael Warnock win the 2028 Democratic presidential nomination? | `0xdce84960dce38aa4a5800a5eba7c9ac34d2ce49ba9d44c42572c472d468af264` |
| 0 |  | Will Gavin Newsom win the 2028 Democratic presidential nomination? | `0x0f49db97f71c68b1e42a6d16e3de93d85dbf7d4148e3f018eb79e88554be9f75` |
| 0 |  | Will Jared Polis win the 2028 Democratic presidential nomination? | `0x8fbcb151e2c988df5a43abb02298014b7daf34c008f3eed9188dd16a2a19bec1` |
| 0 |  | Will Michelle Obama win the 2028 Democratic presidential nomination? | `0x3e218c99a1335641b3a5ee6c887521d19b0c28fddd6b99c254a07968e35c0b1b` |
