---
type: "twitter-thread"
source: "https://x.com/AlterEgo_eth/status/2054170220777132371?s=20"
author: "AlterEgo_eth"
status_id: "2054170220777132371"
status: "full_content_imported"
primary_family: "weather_event_discovery"
priority: "high"
relevance: "direct_edge"
tags: ["source/twitter", "polymarket", "research", "full-content"]
---
# Full Thread - AlterEgo_eth - 2054170220777132371

## Source
https://x.com/AlterEgo_eth/status/2054170220777132371?s=20

## Title
How a Weather Trading Bot Automatically Finds Every Relevant Market on Polymarket in Seconds

## Extraction Summary
- Relevance: `direct_edge`
- Primary family: `weather_event_discovery`
- Priority: `high`
- Families: `weather_event_discovery`

## Actionable Takeaways
- For each weather thread claim, replay forecast update times against market mid-price changes and spread.

## Hypotheses
### weather_event_discovery
- Thesis: Weather markets can be found and repriced faster by mapping forecast updates to active Polymarket markets.
- Value type: `market_selection`
- Required data: `market metadata`, `weather API snapshots`, `forecast timestamps`, `orderbooks`, `trades`
- First test: For each weather thread claim, replay forecast update times against market mid-price changes and spread.
- Risk: Forecast source mismatch or ambiguous market wording can create false positives.
- Priority: `high`

## Evidence
- highest-temperature-in-{city}-on-{month}-{day}-{year}
- Example: highest-temperature-in-seoul-on-may-15-2026
- Inside - all markets for that event: every temperature bin with its own market_id, question text, and price
- > Step 3 - Parse the temperature range from the question text
- "Will the high temperature in Seoul be between 22-23°C on May 15?" or "28°C or higher" / "15°C or below"

## Caveats
- Do not treat posted PnL, win rate, or screenshots as evidence until reproduced locally.

## Raw Thread
```text
From slug generation to parsing outcome prices - full technical breakdown

Using only two Gamma API endpoints

> Step 1 - Build the event slug

Polymarket names events using a standard pattern

For each city and date the bot builds a slug like this:
highest-temperature-in-{city}-on-{month}-{day}-{year}

Example: highest-temperature-in-seoul-on-may-15-2026

This lets you find the exact market without iterating through hundreds of events

> Step 2 - Query the Gamma API by slug

GET https://gamma-api.polymarket.com/events?slug={slug}

The response is an array of events. Take the first element

Inside - all markets for that event: every temperature bin with its own market_id, question text, and price

> Step 3 - Parse the temperature range from the question text

Each bin is described in plain text like:
"Will the high temperature in Seoul be between 22-23°C on May 15?" or "28°C or higher" / "15°C or below"

The bot parses this text with a regex and extracts the lower and upper boundary of the bucket

Edge buckets get sentinel values: -999 for the lower boundary of "or below" and 999 for the upper boundary of "or higher"

> Step 4 - Get the price of each bucket

GET https://gamma-api.polymarket.com/markets/{market_id}

The outcome Prices field returns a JSON string with two prices - YES and NO

prices = json.loads(data.get("outcomePrices", "[0.5,0.5]"))yes_price = float(prices[0])

This is the current market-implied probability of the outcome

Just two Gamma API endpoints cover the full market discovery cycle:
• /events?slug= - find the event by city and date
• /markets/{id} - get the price of each bucket

No auth required on either of them
```
