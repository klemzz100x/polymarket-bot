---
type: "twitter-thread"
source: "https://x.com/Gustafssonkotte/status/2053758338974838857?s=20"
author: "Gustafssonkotte"
status_id: "2053758338974838857"
status: "full_content_imported"
primary_family: "simplification_robustness"
priority: "high"
relevance: "direct_edge"
tags: ["source/twitter", "polymarket", "research", "full-content"]
---
# Full Thread - Gustafssonkotte - 2053758338974838857

## Source
https://x.com/Gustafssonkotte/status/2053758338974838857?s=20

## Title
Deleted half my bot's code and it started winning

## Extraction Summary
- Relevance: `direct_edge`
- Primary family: `simplification_robustness`
- Priority: `high`
- Families: `simplification_robustness`, `crypto_5m_microstructure`, `behavioral_bias_fade`, `bot_tooling_stack`, `weather_event_discovery`

## Actionable Takeaways
- Compare simple baseline strategies against complex variants with identical data and execution assumptions.
- Rebuild 5m windows and test minute-1 direction, reversal, momentum, spread, and fill assumptions.
- Label jump events and test reversion only after spread stabilizes and depth returns.
- Convert useful tooling claims into runbook/dashboard/alert requirements, not strategy candidates.

## Hypotheses
### simplification_robustness
- Thesis: Simpler strategies and smaller execution surfaces may outperform complex bots by reducing failure modes.
- Value type: `engineering_edge`
- Required data: `strategy variants`, `code complexity metrics`, `paper/shadow performance`, `error logs`
- First test: Compare simple baseline strategies against complex variants with identical data and execution assumptions.
- Risk: Over-simplifying can remove real risk controls or necessary market filters.
- Priority: `medium`

### crypto_5m_microstructure
- Thesis: Very short crypto markets may have repeatable early-window patterns if CEX microstructure leads Polymarket.
- Value type: `pricing_signal`
- Required data: `Binance second data`, `Polymarket 5m orderbooks`, `trades`, `market start/end times`
- First test: Rebuild 5m windows and test minute-1 direction, reversal, momentum, spread, and fill assumptions.
- Risk: Backtest leakage, survivorship bias, and queue priority can make a paper edge non-executable.
- Priority: `high`

### behavioral_bias_fade
- Thesis: Behavioral narratives can become fade candidates when price jumps are unsupported by durable depth.
- Value type: `pricing_signal`
- Required data: `price jumps`, `volume spikes`, `orderbook imbalance`, `news labels`, `reversion windows`
- First test: Label jump events and test reversion only after spread stabilizes and depth returns.
- Risk: What looks like bias may be correct information arrival.
- Priority: `medium`

### bot_tooling_stack
- Thesis: Tooling threads can improve the bot's operating model even when they do not contain a trading signal.
- Value type: `ops_infra`
- Required data: `runbooks`, `service health`, `alerts`, `operator actions`, `incident logs`
- First test: Convert useful tooling claims into runbook/dashboard/alert requirements, not strategy candidates.
- Risk: Tool fascination can distract from measurable market edge.
- Priority: `medium`

## Evidence
- I deleted half the codebase: the voter, the tier table, "fair probability", "edge".
- Order walls across multiple exchanges (Binance, Bybit, OKX, Coinbase)
- On a 5-minute market, the last 90 seconds are statistically more predictable than the first three minutes.
- Daily bias (24h trend blocks the opposite side for the day)

## Caveats
- Do not treat posted PnL, win rate, or screenshots as evidence until reproduced locally.

## Raw Thread
```text
TL;DR
The bot traded BTC on Polymarket. WR was 41% on 17 trades, balance was creeping down. I deleted half the codebase: the voter, the tier table, "fair probability", "edge". Rewrote the brain from scratch.
Day 1 after release: 33 trades, 60% WR, balance in the green.
The main fix wasn't new indicators. The main fix was a conflict detector between signals. One check that removed the false entries the system should never have been making.
Six days ago I thought I had a bad brain
I was looking at the numbers and thinking: the model is bad. Need more indicators, better weights, more precise calibration.
Sat down to audit. By the end of the day I had three discoveries.
First bug. The voter would output "top signal, max position size". But between the voter and the entry function, the tier field was getting lost in the handoff. Every trade applied the minimum size. All my "confident" entries were undersized.
Second bug. When the drawdown limit triggered, the code wrote "PAUSED" to the log in pretty red color, and returned success in the risk check. The bot kept trading. Defense in depth, turned off by default.
Third bug, and this one was the worst. The order placement had a fail-safe: "if the order doesn't confirm within a couple of seconds, assume it filled." Half the "wins" in the logs never opened on the exchange. I was looking at win/loss stats and making decisions on data that was lying.
Three silent bugs were corrupting data for weeks. I was looking at 41% WR and thinking my brain was bad. The brain was fine. It was just making decisions on broken data.
I fixed the three bugs. Added a check of real balance before and after each order. Rewrote the fail-safe so on timeout it returned "nothing happened" instead of "WIN".
Looked at the clean data.
It was worse.
The brain was broken at its foundation
Once phantom WINs were out of the stats, real WR dropped even lower. Worse than a coin flip.
The problem wasn't the bugs. The bugs were symptoms. The problem was the brain's architecture.
The old system asked one weighted question:
The old system asked one weighted question:
indicators vote
        ↓
sum the weights
        ↓
get a number from -1 to +1
        ↓
number → category (top / mid / weak / minimal)
        ↓
category → "fair probability", a hardcoded number
        ↓
edge = "fair probability" - market price - fee
        ↓
if edge >= threshold, ENTER
Three fundamental problems.
Three fundamental problems.
First. The "probability" table wasn't a probability, it was a lookup table. The numbers were picked at random six months ago. Zero connection to real outcome frequencies. When I calculated WR by category on live data:
Top category: 0 of 1
Mid: 1 of 2
Weak: 2 of 4
Category parse miss: 4 of 8
Parse misses were winning more often than "top" trades. That's not calibration. That's noise dressed up as confidence.
Second. The edge formula inverted the sign. The bot entered with negative edge and won. Entered with large positive edge and lost.
Low "model confidence": 57% WR
Mid: 20%
High: 0%
The more "confident" the model was, the worse it performed. The formula wasn't predicting outcomes at all.
Third, and the main one. When indicators disagreed, the system didn't notice.
Trend screams "up". Momentum says "down". Levels are silent. Average with weights, get a slightly positive number, hits "mid category, enter".
That's not confidence. That's an average of contradictions.
And the bot entered.
Delete, don't add
I deleted all of it. The voter, the category table, "fair probability", the edge formula, nine hardcoded weights.
Rewrote it. Three modules, one brain.
Q1. Where is the price going?
MTF trends across multiple timeframes
EMA cross on 5-min candles
EMA 50 / EMA 200 as a structural filter
VWAP deviation
Q2. Where are the magnets and barriers?
Structural highs and lows
Liquidity sweep detection
Order walls across multiple exchanges (Binance, Bybit, OKX, Coinbase)
Anti-spoof filter against fake walls
Q3. Is momentum for or against?
RSI on two periods
Bollinger Bands (squeeze + breakout)
Parabolic SAR
Fair Value Gap (FVG)
Orderbook pressure
Each module combines several sources internally and outputs a single probability from 0 to 1. Plus a second number: signal strength, meaning how confidently the module is saying anything at all.
The old system asked one weighted question. The new one asks three and watches how well they agree.
Conflict filter: not a feature, a fix
Three answers come into the brain. I calculate three values:
python
confidence = weighted_average(p_trend, p_level, p_momentum)
strength   = average(s_trend, s_level, s_momentum)
spread     = max(p_trend, p_level, p_momentum) - min(...)
Confidence is the weighted average of the answers. Strength is the average across module strengths. And spread is the gap between the highest and lowest answer.
If the spread is too large, the modules are disagreeing too much. Don't trade.
python
if spread > THRESHOLD:
    return SKIP("internal_conflict")
An example from live logs:
Q1 TREND:    p_up=0.76  S=0.51
Q2 LEVELS:   p_up=0.67  S=0.34
Q3 MOMENTUM: p_up=0.10  S=0.80   (RSI overbought, waiting for a pullback)
SKIP: internal_conflict, spread=0.66
Trend and levels are screaming "up". Momentum is screaming "down" because RSI is maxed out and waiting for a correction. The old system would have averaged the votes and entered long. The new one sees the conflict and passes.
The conflict filter doesn't add new logic. It removes false entries the system should never have been making. It's not an improvement. It's a fix.
What percentage of losses in the old version were exactly that, conflicting setups averaged into a "signal"? I don't know exactly. But if even half, then 70% WR is reachable without changing anything else. Just less noise on entry.
What a good setup looks like
For contrast, an entry v4 approved:
Q1 TREND:    p_up=0.20  S=0.59   (all TFs down, EMA down, VWAP down)
Q2 LEVELS:   p_up=0.18  S=0.65   (real BID wall, magnet down)
Q3 MOMENTUM: p_up=0.35  S=0.30   (RSI and BB say "oversold", but no reversal)
 ENTER DOWN: conf=0.76 strength=0.49 spread=0.15
All three modules looking down. Momentum is slightly less confident because RSI is near the lower Bollinger band, hinting at oversold conditions. But it doesn't contradict. Spread is small. Confidence is high.
ENTER DOWN. WIN.
Time-aware sizing
On a 5-minute market, the last 90 seconds are statistically more predictable than the first three minutes. Price has already chosen a direction.
Position size scales with time to close:
python
def time_factor(mins_left):
    if mins_left >= 4.0:  return 0.7    # early, noisy
    if mins_left >= 3.0:  return 0.85
    if mins_left >= 2.0:  return 1.0
    if mins_left >= 1.0:  return 1.2
    return 1.3                          # late, sharper
The final size:
size = base * confidence * (1 - spread) * strength * time_factor
The more disagreement between modules (spread), the smaller the size. The closer to close and the cleaner the setup, the larger. No categories. No lookup table. Just math on live data.
Trading hours: no trading at night
The first night after v4, the bot drew down over eight hours on low liquidity. Bitcoin wasn't moving, the bot was burning spreads. All protections fired: the drawdown limit stopped it and put it on pause.
But protection is the last line of defense.
Bitcoin moves when institutions move. Trading at 3 AM on a flat tape is just paying spreads.
Added a schedule: weekdays, daytime hours Moscow time. Weekends are fully blocked.
Important detail: during off hours the bot doesn't shut down. WebSocket feeds keep accumulating, candles keep building, walls keep being tracked. Monday morning the bot starts with full history from the weekend. Only new entries are blocked.
Protections in firing order
Trading hours. Outside working hours, entries are blocked.
Weekend block. Saturday and Sunday fully off.
Loss streak. Three losses in a row put the bot on a short pause.
Drawdown. A sharp balance drop stops trading.
Daily loss. Daily loss limit stops the bot until tomorrow.
Internal conflict. Too large a spread between modules cancels the entry.
Low confidence. Weak overall confidence cancels the entry.
Low strength. Weak overall signal cancels the entry.
Numbers
Before (old system, two weeks): 17 trades, WR 41%, direction guessed 47% of the time, P&L in the red.
After (v4, day 1): 33 trades, WR 60%, direction guessed 60%. UP side won 61% of the time, DOWN side 58%. P&L in the green.
Symmetry between sides is back. No more systematic skew (the old bot longed a falling market seven times in a row).
Source of truth: Polymarket exports, not the bot's internal counter. The internal counter isn't fully cleaned of the phantom WIN legacy. Its fix is on the TODO list.
Goal: 70% WR over the next 100+ trades.
Simple math. v4 showed 60% on 33 trades. The conflict filter is running loose for now: average spread in logs is well below threshold. Tighten the threshold and a noticeable chunk of trades gets cut, mostly the bad ones. Plus confidence calibration on real data.
70% is a calibration question, not a rewrite question.
Stack
Python
Chainlink Data Streams for BTC price feed, no exchange API in the path
Polymarket CLOB for execution
Multi-exchange WebSocket orderbook feeds
Ubuntu VPS
TODO
Make momentum trend-aware (oscillator extremes are noise in a strong trend, signal in chop)
Daily bias (24h trend blocks the opposite side for the day)
Volatility gate (dead tape, SKIP)
Fix the internal counter
All of these are only if live data confirms the need. Not fixing what works.
The main lesson
I thought the bot was losing because the brain was bad. Turns out the brain was making decisions on broken data, and the brain's architecture itself was averaging contradictions into a "signal".
The bot wasn't losing because it was bad. The bot was losing because I was listening to its broken brain.
Every loss was a signal. I was averaging them into an "entry".
The hard part wasn't writing new indicators.
The hard part was deleting the old ones that pretended to work.
```
