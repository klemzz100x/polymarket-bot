#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

import asyncpg
import httpx

from polybot.core.compat import UTC
from polybot.core.config import get_settings
from polybot.knowledge.obsidian import ObsidianVault
from polybot.polymarket.api import PolymarketClient
from polybot.resources.markdown import render_frontmatter


CREATE_WEATHER_TABLE_SQL = """
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.weather_market_radar_ticks (
    id BIGSERIAL PRIMARY KEY,
    scan_id TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    event_id TEXT,
    event_slug TEXT,
    event_title TEXT,
    market_id TEXT,
    condition_id TEXT,
    market_slug TEXT,
    question TEXT NOT NULL,
    weather_family TEXT NOT NULL,
    location_hint TEXT,
    threshold_hint TEXT,
    end_date TIMESTAMPTZ,
    volume NUMERIC(38, 18),
    liquidity NUMERIC(38, 18),
    token_count INTEGER NOT NULL DEFAULT 0,
    best_yes_bid NUMERIC(38, 18),
    best_yes_ask NUMERIC(38, 18),
    best_no_bid NUMERIC(38, 18),
    best_no_ask NUMERIC(38, 18),
    pair_cost NUMERIC(38, 18),
    spread NUMERIC(38, 18),
    market_state TEXT NOT NULL,
    rejected_reason TEXT NOT NULL DEFAULT '',
    edge_hypothesis TEXT NOT NULL DEFAULT '',
    source_url TEXT NOT NULL DEFAULT '',
    raw JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_weather_radar_observed
    ON app.weather_market_radar_ticks(observed_at DESC);
CREATE INDEX IF NOT EXISTS ix_weather_radar_scan
    ON app.weather_market_radar_ticks(scan_id);
CREATE INDEX IF NOT EXISTS ix_weather_radar_state_observed
    ON app.weather_market_radar_ticks(market_state, observed_at DESC);
CREATE INDEX IF NOT EXISTS ix_weather_radar_condition_observed
    ON app.weather_market_radar_ticks(condition_id, observed_at DESC);
"""


@dataclass(slots=True)
class WeatherCandidate:
    event_id: str | None
    event_slug: str | None
    event_title: str | None
    market_id: str | None
    condition_id: str | None
    market_slug: str | None
    question: str
    weather_family: str
    location_hint: str | None
    threshold_hint: str | None
    end_date: datetime | None
    volume: Decimal | None
    liquidity: Decimal | None
    token_ids: list[str]
    raw: dict[str, Any]


@dataclass(slots=True)
class WeatherRadarRow:
    candidate: WeatherCandidate
    observed_at: datetime
    best_yes_bid: Decimal | None
    best_yes_ask: Decimal | None
    best_no_bid: Decimal | None
    best_no_ask: Decimal | None
    pair_cost: Decimal | None
    spread: Decimal | None
    market_state: str
    rejected_reason: str
    edge_hypothesis: str


async def main_async() -> int:
    parser = argparse.ArgumentParser(description="Discover and score weather markets without placing orders.")
    parser.add_argument("--limit", type=int, default=40, help="Maximum markets to inspect.")
    parser.add_argument("--event-limit", type=int, default=80, help="Maximum weather events to pull from Gamma.")
    parser.add_argument("--no-db", action="store_true", help="Do not persist scan rows to Postgres.")
    parser.add_argument("--json-out", type=Path, default=Path("resources/edge-tests/weather_market_radar.json"))
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    parser.add_argument("--obsidian", action="store_true", help="Write an Obsidian research note.")
    args = parser.parse_args()

    settings = get_settings()
    scan_id = f"weather-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
    candidates = await discover_weather_candidates(settings, event_limit=args.event_limit, market_limit=args.limit)
    rows = await score_candidates(settings, candidates)

    payload = {
        "scan_id": scan_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": "research_read_only",
        "live_trading": "disabled",
        "candidate_count": len(candidates),
        "rows": [row_to_json(row) for row in rows],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.no_db:
        conn = await asyncpg.connect(resolve_database_url(settings.database_url))
        try:
            await conn.execute(CREATE_WEATHER_TABLE_SQL)
            await persist_rows(conn, scan_id, rows)
        finally:
            await conn.close()

    report_path = None
    if args.obsidian:
        vault = ObsidianVault(args.vault)
        vault.ensure_structure()
        report_path = vault.write_note(
            "Research/Edge-Research",
            "Weather Market Radar",
            render_weather_report(scan_id, rows),
            overwrite=True,
        )

    state_counts: dict[str, int] = {}
    for row in rows:
        state_counts[row.market_state] = state_counts.get(row.market_state, 0) + 1
    print(f"Weather scan={scan_id}")
    print(f"Candidates={len(candidates)} rows={len(rows)} states={state_counts}")
    print(f"JSON={args.json_out}")
    if report_path:
        print(f"Report={report_path}")
    for row in rows[:8]:
        c = row.candidate
        print(
            f"- {row.market_state}: {c.question[:90]} | spread={fmt_decimal(row.spread)} "
            f"pair={fmt_decimal(row.pair_cost)} | {row.rejected_reason}"
        )
    return 0


async def discover_weather_candidates(settings: Any, *, event_limit: int, market_limit: int) -> list[WeatherCandidate]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(settings.polymarket_http_timeout_seconds)) as client:
        response = await client.get(
            f"{settings.polymarket_gamma_api_url}/events",
            params={
                "tag_slug": "weather",
                "active": "true",
                "closed": "false",
                "limit": event_limit,
            },
        )
        response.raise_for_status()
        events = response.json()
    if not isinstance(events, list):
        return []

    candidates: list[WeatherCandidate] = []
    seen_condition_ids: set[str] = set()
    for event in events:
        if not isinstance(event, dict):
            continue
        for market in event.get("markets") or []:
            if not isinstance(market, dict) or not market.get("enableOrderBook"):
                continue
            candidate = candidate_from_market(event, market)
            if not candidate.condition_id or candidate.condition_id in seen_condition_ids:
                continue
            seen_condition_ids.add(candidate.condition_id)
            candidates.append(candidate)

    candidates.sort(
        key=lambda item: (
            item.weather_family != "daily_temperature",
            -(item.volume or Decimal("0")),
            -(item.liquidity or Decimal("0")),
        )
    )
    return candidates[:market_limit]


def candidate_from_market(event: dict[str, Any], market: dict[str, Any]) -> WeatherCandidate:
    question = str(market.get("question") or event.get("title") or "")
    slug = str(market.get("slug") or event.get("slug") or "")
    return WeatherCandidate(
        event_id=str(event.get("id")) if event.get("id") is not None else None,
        event_slug=str(event.get("slug")) if event.get("slug") is not None else None,
        event_title=str(event.get("title")) if event.get("title") is not None else None,
        market_id=str(market.get("id")) if market.get("id") is not None else None,
        condition_id=str(market.get("conditionId")) if market.get("conditionId") is not None else None,
        market_slug=slug,
        question=question,
        weather_family=classify_weather_family(question, slug),
        location_hint=extract_location_hint(question, slug),
        threshold_hint=extract_threshold_hint(question, market),
        end_date=parse_dt(market.get("endDate") or event.get("endDate")),
        volume=to_decimal(market.get("volume") or market.get("volumeNum") or event.get("volume")),
        liquidity=to_decimal(market.get("liquidity") or market.get("liquidityNum") or event.get("liquidity")),
        token_ids=parse_jsonish_list(market.get("clobTokenIds")),
        raw={
            "event": compact_raw(event, exclude=("markets",)),
            "market": compact_raw(market),
        },
    )


async def score_candidates(settings: Any, candidates: list[WeatherCandidate]) -> list[WeatherRadarRow]:
    token_to_candidate: dict[str, WeatherCandidate] = {}
    token_ids: list[str] = []
    for candidate in candidates:
        for token_id in candidate.token_ids[:2]:
            token_to_candidate[token_id] = candidate
            token_ids.append(token_id)

    books_by_token: dict[str, dict[str, Any]] = {}
    async with PolymarketClient(settings) as client:
        for chunk in chunks(token_ids, 80):
            if not chunk:
                continue
            try:
                books = await client.get_orderbooks(chunk)
            except Exception:
                books = []
            for book in books:
                asset_id = str(book.get("asset_id") or book.get("token_id") or "")
                if asset_id:
                    books_by_token[asset_id] = book

    observed_at = datetime.now(UTC)
    rows: list[WeatherRadarRow] = []
    for candidate in candidates:
        yes_book = books_by_token.get(candidate.token_ids[0]) if len(candidate.token_ids) >= 1 else None
        no_book = books_by_token.get(candidate.token_ids[1]) if len(candidate.token_ids) >= 2 else None
        yes_bid, yes_ask = extract_best_prices(yes_book or {})
        no_bid, no_ask = extract_best_prices(no_book or {})
        pair_cost = yes_ask + no_ask if yes_ask is not None and no_ask is not None else None
        spread = pair_cost - Decimal("1") if pair_cost is not None else None
        market_state, rejected_reason = classify_market_state(candidate, yes_ask, no_ask, spread)
        rows.append(
            WeatherRadarRow(
                candidate=candidate,
                observed_at=observed_at,
                best_yes_bid=yes_bid,
                best_yes_ask=yes_ask,
                best_no_bid=no_bid,
                best_no_ask=no_ask,
                pair_cost=pair_cost,
                spread=spread,
                market_state=market_state,
                rejected_reason=rejected_reason,
                edge_hypothesis=edge_hypothesis_for(candidate),
            )
        )
    rows.sort(
        key=lambda row: (
            state_rank(row.market_state),
            row.spread if row.spread is not None else Decimal("99"),
            -(row.candidate.volume or Decimal("0")),
        )
    )
    return rows


def classify_market_state(
    candidate: WeatherCandidate,
    yes_ask: Decimal | None,
    no_ask: Decimal | None,
    spread: Decimal | None,
) -> tuple[str, str]:
    if len(candidate.token_ids) < 2:
        return "NO_TOKENS", "missing YES/NO token ids"
    if yes_ask is None or no_ask is None:
        return "NO_BOOK", "missing public orderbook on one side"
    if spread is not None and spread < Decimal("0"):
        return "PAIR_ARB_WATCH", "YES+NO ask below 1 before fees/slippage checks"
    if spread is not None and spread <= Decimal("0.04"):
        return "FORECAST_WATCH", "tight enough to compare against external forecast fair value"
    if spread is not None and spread <= Decimal("0.10"):
        return "WATCH", "spread acceptable for monitoring, not an edge by itself"
    return "ILLIQUID", "spread above 10%; wait or only use for research"


def classify_weather_family(question: str, slug: str) -> str:
    text = f"{question} {slug}".lower()
    if "highest temperature" in text or "hottest" in text or "temperature" in text:
        return "daily_temperature"
    if "rain" in text or "precipitation" in text:
        return "precipitation"
    if "hurricane" in text or "storm" in text or "landfall" in text:
        return "hurricane_storm"
    if "snow" in text:
        return "snow"
    if "earthquake" in text or "volcano" in text or "meteor" in text:
        return "natural_disaster"
    if "ice" in text or "climate" in text or "record" in text:
        return "climate"
    return "weather_other"


def extract_location_hint(question: str, slug: str) -> str | None:
    patterns = (
        r"highest temperature in ([A-Za-z .'-]+?) on ",
        r"temperature in ([A-Za-z .'-]+?) on ",
        r"in ([A-Za-z .'-]+?) by ",
        r"in ([A-Za-z .'-]+?) before ",
        r"in ([A-Za-z .'-]+?)\?",
    )
    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            return match.group(1).strip(" ?")
    slug_match = re.search(r"highest-temperature-in-([a-z0-9-]+?)-on-", slug)
    if slug_match:
        return slug_match.group(1).replace("-", " ").title()
    return None


def extract_threshold_hint(question: str, market: dict[str, Any]) -> str | None:
    group_title = market.get("groupItemTitle")
    threshold = market.get("groupItemThreshold")
    if group_title:
        return str(group_title)
    if threshold:
        return str(threshold)
    match = re.search(r"(\d+(?:\.\d+)?\s?(?:°?[CF]|kt|inches|mm|or higher|or lower|or below))", question)
    if match:
        return match.group(1)
    return None


def edge_hypothesis_for(candidate: WeatherCandidate) -> str:
    if candidate.weather_family == "daily_temperature":
        return "Replay official forecast updates vs market mid; edge only if forecast-implied bucket diverges after spread."
    if candidate.weather_family == "hurricane_storm":
        return "Track NHC advisories; market should move around formation/category/landfall updates."
    if candidate.weather_family == "precipitation":
        return "Track high-frequency forecast precipitation probability and station rules."
    if candidate.weather_family == "climate":
        return "Slow research market; use official dataset release timing, not HFT."
    return "Use only after resolution source and external data feed are mapped."


def extract_best_prices(book: dict[str, Any]) -> tuple[Decimal | None, Decimal | None]:
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    bid_prices = [price for price in (to_decimal(level.get("price")) for level in bids) if price is not None]
    ask_prices = [price for price in (to_decimal(level.get("price")) for level in asks) if price is not None]
    best_bid = max(bid_prices) if bid_prices else None
    best_ask = min(ask_prices) if ask_prices else None
    return best_bid, best_ask


async def persist_rows(conn: asyncpg.Connection, scan_id: str, rows: list[WeatherRadarRow]) -> None:
    for row in rows:
        c = row.candidate
        await conn.execute(
            """
            INSERT INTO app.weather_market_radar_ticks (
                scan_id, observed_at, event_id, event_slug, event_title, market_id, condition_id,
                market_slug, question, weather_family, location_hint, threshold_hint, end_date,
                volume, liquidity, token_count, best_yes_bid, best_yes_ask, best_no_bid,
                best_no_ask, pair_cost, spread, market_state, rejected_reason,
                edge_hypothesis, source_url, raw
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7,
                $8, $9, $10, $11, $12, $13,
                $14, $15, $16, $17, $18, $19,
                $20, $21, $22, $23, $24,
                $25, $26, $27::jsonb
            )
            """,
            scan_id,
            row.observed_at,
            c.event_id,
            c.event_slug,
            c.event_title,
            c.market_id,
            c.condition_id,
            c.market_slug,
            c.question,
            c.weather_family,
            c.location_hint,
            c.threshold_hint,
            c.end_date,
            c.volume,
            c.liquidity,
            len(c.token_ids),
            row.best_yes_bid,
            row.best_yes_ask,
            row.best_no_bid,
            row.best_no_ask,
            row.pair_cost,
            row.spread,
            row.market_state,
            row.rejected_reason,
            row.edge_hypothesis,
            f"https://polymarket.com/event/{c.event_slug}" if c.event_slug else "",
            json.dumps(c.raw, default=str),
        )


def render_weather_report(scan_id: str, rows: list[WeatherRadarRow]) -> str:
    state_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    for row in rows:
        state_counts[row.market_state] = state_counts.get(row.market_state, 0) + 1
        family_counts[row.candidate.weather_family] = family_counts.get(row.candidate.weather_family, 0) + 1
    return f"""{render_frontmatter({"type": "weather-market-radar", "tags": ["research", "weather", "edge", "paper-only"]})}
# Weather Market Radar

Generated at: `{datetime.now(UTC).isoformat()}`

Scan ID: `{scan_id}`

Mode: `research_read_only`. No live trading, no order placement, no private key usage.

## Verdict
- Best thread-derived edge: weather markets are not HFT first; they are objective external-data markets where forecast/advisory updates can lead Polymarket repricing.
- Promotion rule: do not treat a market as tradable until its resolution source, external forecast feed, spread, and depth are mapped.
- Next build step: add forecast snapshots for `daily_temperature` and NHC advisory timestamps for `hurricane_storm`.

## State Counts
{bullets([f"{key}: {value}" for key, value in sorted(state_counts.items())])}

## Family Counts
{bullets([f"{key}: {value}" for key, value in sorted(family_counts.items())])}

## Top Markets
{render_rows_table(rows[:20])}
"""


def render_rows_table(rows: list[WeatherRadarRow]) -> str:
    if not rows:
        return "No markets found."
    lines = [
        "| State | Spread | Family | Market | Location | Hypothesis |",
        "|---|---:|---|---|---|---|",
    ]
    for row in rows:
        c = row.candidate
        lines.append(
            f"| {row.market_state} | {fmt_decimal(row.spread)} | {c.weather_family} | "
            f"{c.question[:80]} | {c.location_hint or ''} | {row.edge_hypothesis[:90]} |"
        )
    return "\n".join(lines)


def row_to_json(row: WeatherRadarRow) -> dict[str, Any]:
    payload = asdict(row)
    return json.loads(json.dumps(payload, default=str))


def compact_raw(raw: dict[str, Any], exclude: tuple[str, ...] = ()) -> dict[str, Any]:
    excluded = set(exclude)
    keep = {}
    for key, value in raw.items():
        if key in excluded:
            continue
        if key in {"description"} and isinstance(value, str) and len(value) > 1000:
            keep[key] = value[:1000] + "..."
        else:
            keep[key] = value
    return keep


def parse_jsonish_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    return []


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def to_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def state_rank(state: str) -> int:
    ranks = {
        "PAIR_ARB_WATCH": 0,
        "FORECAST_WATCH": 1,
        "WATCH": 2,
        "ILLIQUID": 3,
        "NO_BOOK": 4,
        "NO_TOKENS": 5,
    }
    return ranks.get(state, 9)


def fmt_decimal(value: Decimal | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- none"


def normalize_database_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


def resolve_database_url(settings_url: str) -> str:
    url = os.getenv("DATABASE_URL", settings_url)
    normalized = normalize_database_url(url)
    if "@localhost:" in normalized:
        normalized = normalized.replace("@localhost:", "@postgres:", 1)
    if "@127.0.0.1:" in normalized:
        normalized = normalized.replace("@127.0.0.1:", "@postgres:", 1)
    return normalized


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async()))
