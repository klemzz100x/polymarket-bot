#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from math import erf, sqrt
import json
import os
from pathlib import Path
import re
from typing import Any

import asyncpg
import httpx

from polybot.core.config import get_settings
from polybot.knowledge.obsidian import ObsidianVault
from polybot.resources.markdown import render_frontmatter


CREATE_FORECAST_EDGE_TABLE_SQL = """
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.weather_forecast_edges (
    id BIGSERIAL PRIMARY KEY,
    scan_id TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    radar_tick_id BIGINT REFERENCES app.weather_market_radar_ticks(id) ON DELETE SET NULL,
    condition_id TEXT,
    question TEXT NOT NULL,
    location_hint TEXT NOT NULL,
    target_date DATE,
    threshold_hint TEXT,
    forecast_max_c NUMERIC(18, 8),
    model_sigma_c NUMERIC(18, 8),
    fair_yes NUMERIC(18, 8),
    market_mid NUMERIC(18, 8),
    best_yes_bid NUMERIC(18, 8),
    best_yes_ask NUMERIC(18, 8),
    best_no_ask NUMERIC(18, 8),
    spread NUMERIC(18, 8),
    edge_yes NUMERIC(18, 8),
    edge_no NUMERIC(18, 8),
    action_bias TEXT NOT NULL,
    model_state TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    source_name TEXT NOT NULL DEFAULT 'open-meteo-proxy',
    source_url TEXT NOT NULL DEFAULT '',
    raw JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_weather_forecast_edges_observed
    ON app.weather_forecast_edges(observed_at DESC);
CREATE INDEX IF NOT EXISTS ix_weather_forecast_edges_state_observed
    ON app.weather_forecast_edges(model_state, observed_at DESC);
CREATE INDEX IF NOT EXISTS ix_weather_forecast_edges_scan
    ON app.weather_forecast_edges(scan_id);
"""

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

STATION_COORDS: dict[str, dict[str, Any]] = {
    "EGLC": {
        "name": "London City Airport Station",
        "latitude": 51.5053,
        "longitude": 0.0553,
        "timezone": "Europe/London",
    },
    "RKSI": {
        "name": "Incheon Intl Airport Station",
        "latitude": 37.4602,
        "longitude": 126.4407,
        "timezone": "Asia/Seoul",
    },
    "KAUS": {
        "name": "Austin-Bergstrom International Airport Station",
        "latitude": 30.1975,
        "longitude": -97.6664,
        "timezone": "America/Chicago",
    },
}


@dataclass(slots=True)
class ForecastEdge:
    scan_id: str
    observed_at: datetime
    radar_tick_id: int
    condition_id: str | None
    question: str
    location_hint: str
    target_date: date | None
    threshold_hint: str | None
    forecast_max_c: Decimal | None
    model_sigma_c: Decimal | None
    fair_yes: Decimal | None
    market_mid: Decimal | None
    best_yes_bid: Decimal | None
    best_yes_ask: Decimal | None
    best_no_ask: Decimal | None
    spread: Decimal | None
    edge_yes: Decimal | None
    edge_no: Decimal | None
    action_bias: str
    model_state: str
    reason: str
    source_url: str
    source_adapter: str
    raw: dict[str, Any]


async def main_async() -> int:
    parser = argparse.ArgumentParser(description="Score weather markets against an external forecast proxy.")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--min-edge", type=Decimal, default=Decimal("0.08"))
    parser.add_argument("--max-spread", type=Decimal, default=Decimal("0.04"))
    parser.add_argument("--no-db", action="store_true")
    parser.add_argument("--json-out", type=Path, default=Path("resources/edge-tests/weather_forecast_edges.json"))
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    parser.add_argument("--obsidian", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    conn = await asyncpg.connect(resolve_database_url(settings.database_url))
    try:
        rows = await fetch_latest_weather_rows(conn, args.limit)
        edges = await score_rows(rows, min_edge=args.min_edge, max_spread=args.max_spread)
        if not args.no_db:
            await conn.execute(CREATE_FORECAST_EDGE_TABLE_SQL)
            await persist_edges(conn, edges)
    finally:
        await conn.close()

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": "research_read_only",
        "live_trading": "disabled",
        "source": "open-meteo-proxy",
        "warning": "Forecast proxy only; verify Polymarket resolution source before trading.",
        "edges": [edge_to_json(edge) for edge in edges],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    report_path = None
    if args.obsidian:
        vault = ObsidianVault(args.vault)
        vault.ensure_structure()
        report_path = vault.write_note(
            "Research/Edge-Research",
            "Weather Forecast Edge Scores",
            render_report(edges, min_edge=args.min_edge, max_spread=args.max_spread),
            overwrite=True,
        )

    counts: dict[str, int] = {}
    for edge in edges:
        counts[edge.model_state] = counts.get(edge.model_state, 0) + 1
    print(f"Weather forecast edges scored={len(edges)} states={counts}")
    print(f"JSON={args.json_out}")
    if report_path:
        print(f"Report={report_path}")
    for edge in sorted(edges, key=edge_sort_key)[:10]:
        print(
            f"- {edge.model_state} {edge.action_bias}: {edge.question[:84]} "
            f"fair={fmt_prob(edge.fair_yes)} mid={fmt_prob(edge.market_mid)} "
            f"edgeY={fmt_prob(edge.edge_yes)} edgeN={fmt_prob(edge.edge_no)} | {edge.reason}"
        )
    return 0


async def fetch_latest_weather_rows(conn: asyncpg.Connection, limit: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        WITH latest_scan AS (
            SELECT scan_id
            FROM app.weather_market_radar_ticks
            ORDER BY observed_at DESC
            LIMIT 1
        )
        SELECT id, scan_id, observed_at, condition_id, question, location_hint, threshold_hint,
               end_date, best_yes_bid, best_yes_ask, best_no_ask, spread, market_state, raw
        FROM app.weather_market_radar_ticks
        WHERE scan_id = (SELECT scan_id FROM latest_scan)
          AND market_state IN ('FORECAST_WATCH', 'WATCH')
          AND weather_family = 'daily_temperature'
          AND location_hint IS NOT NULL
          AND threshold_hint IS NOT NULL
        ORDER BY spread ASC NULLS LAST
        LIMIT $1
        """,
        limit,
    )


async def score_rows(rows: list[asyncpg.Record], *, min_edge: Decimal, max_spread: Decimal) -> list[ForecastEdge]:
    async with httpx.AsyncClient(timeout=25) as client:
        geo_cache: dict[str, dict[str, Any] | None] = {}
        edges: list[ForecastEdge] = []
        for row in rows:
            location = str(row["location_hint"])
            source = extract_resolution_source(row)
            station = station_from_source(source)
            if station:
                geo = STATION_COORDS.get(station)
            else:
                if location not in geo_cache:
                    geo_cache[location] = await geocode_location(client, location)
                geo = geo_cache[location]
            target_date = parse_target_date(str(row["question"]), row["end_date"])
            threshold = parse_threshold(str(row["threshold_hint"] or row["question"]))
            forecast = None
            if geo and target_date:
                forecast = await fetch_forecast_max_c(client, geo, target_date)
            edge = build_edge(
                row,
                geo,
                forecast,
                target_date,
                threshold,
                source=source,
                station=station,
                min_edge=min_edge,
                max_spread=max_spread,
            )
            edges.append(edge)
    return edges


async def geocode_location(client: httpx.AsyncClient, location: str) -> dict[str, Any] | None:
    response = await client.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": location, "count": 1, "language": "en", "format": "json"},
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    return results[0] if results else None


async def fetch_forecast_max_c(client: httpx.AsyncClient, geo: dict[str, Any], target_date: date) -> dict[str, Any] | None:
    response = await client.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "daily": "temperature_2m_max",
            "temperature_unit": "celsius",
            "timezone": "auto",
            "start_date": target_date.isoformat(),
            "end_date": target_date.isoformat(),
        },
    )
    response.raise_for_status()
    payload = response.json()
    values = ((payload.get("daily") or {}).get("temperature_2m_max") or [])
    if not values:
        return None
    return {"forecast_max_c": values[0], "payload": payload}


def build_edge(
    row: asyncpg.Record,
    geo: dict[str, Any] | None,
    forecast: dict[str, Any] | None,
    target_date: date | None,
    threshold: tuple[str, Decimal, Decimal] | None,
    *,
    source: dict[str, str],
    station: str | None,
    min_edge: Decimal,
    max_spread: Decimal,
) -> ForecastEdge:
    observed_at = row["observed_at"]
    best_yes_bid = to_decimal(row["best_yes_bid"])
    best_yes_ask = to_decimal(row["best_yes_ask"])
    best_no_ask = to_decimal(row["best_no_ask"])
    spread = to_decimal(row["spread"])
    market_mid = None
    if best_yes_bid is not None and best_yes_ask is not None:
        market_mid = (best_yes_bid + best_yes_ask) / Decimal("2")

    forecast_max_c = to_decimal(forecast.get("forecast_max_c")) if forecast else None
    sigma = sigma_for(target_date, observed_at) if target_date else None
    fair_yes = None
    reason_parts = []
    if not geo:
        reason_parts.append("geocode missing")
    if target_date is None:
        reason_parts.append("target date missing")
    if threshold is None:
        reason_parts.append("threshold parse missing")
    if forecast_max_c is None:
        reason_parts.append("forecast missing")
    source_adapter = "open-meteo-city-proxy"
    source_url = "https://open-meteo.com/"
    if station and station in STATION_COORDS:
        source_adapter = f"open-meteo-resolution-station-proxy:{station}"
        source_url = source.get("url") or source_url
    elif source.get("kind") == "hko":
        source_adapter = "open-meteo-city-proxy:hko-resolution-mismatch"
        source_url = source.get("url") or source_url
        reason_parts.append("exact HKO forecast adapter missing")
    if threshold and forecast_max_c is not None and sigma is not None:
        _mode, low_c, high_c = threshold
        fair_yes = interval_probability(forecast_max_c, sigma, low_c, high_c)

    edge_yes = fair_yes - best_yes_ask if fair_yes is not None and best_yes_ask is not None else None
    edge_no = (Decimal("1") - fair_yes) - best_no_ask if fair_yes is not None and best_no_ask is not None else None
    action_bias, model_state, reason = classify_edge(
        edge_yes=edge_yes,
        edge_no=edge_no,
        spread=spread,
        min_edge=min_edge,
        max_spread=max_spread,
        blockers=reason_parts,
    )

    return ForecastEdge(
        scan_id=row["scan_id"],
        observed_at=observed_at,
        radar_tick_id=int(row["id"]),
        condition_id=row["condition_id"],
        question=row["question"],
        location_hint=row["location_hint"],
        target_date=target_date,
        threshold_hint=row["threshold_hint"],
        forecast_max_c=forecast_max_c,
        model_sigma_c=sigma,
        fair_yes=fair_yes,
        market_mid=market_mid,
        best_yes_bid=best_yes_bid,
        best_yes_ask=best_yes_ask,
        best_no_ask=best_no_ask,
        spread=spread,
        edge_yes=edge_yes,
        edge_no=edge_no,
        action_bias=action_bias,
        model_state=model_state,
        reason=reason,
        source_url=source_url,
        source_adapter=source_adapter,
        raw={
            "geocode": geo,
            "forecast": forecast,
            "threshold": threshold,
            "resolution_source": source,
            "station": station,
            "blockers": reason_parts,
        },
    )


def classify_edge(
    *,
    edge_yes: Decimal | None,
    edge_no: Decimal | None,
    spread: Decimal | None,
    min_edge: Decimal,
    max_spread: Decimal,
    blockers: list[str],
) -> tuple[str, str, str]:
    if blockers:
        return "NONE", "MODEL_BLOCKED", "; ".join(blockers)
    if spread is None or spread > max_spread:
        return "NONE", "SPREAD_BLOCKED", f"spread {fmt_prob(spread)} above max {fmt_prob(max_spread)}"
    yes = edge_yes or Decimal("-99")
    no = edge_no or Decimal("-99")
    if yes >= min_edge and yes >= no:
        return "YES", "EDGE_CANDIDATE", f"YES proxy edge {fmt_prob(yes)} >= {fmt_prob(min_edge)}"
    if no >= min_edge:
        return "NO", "EDGE_CANDIDATE", f"NO proxy edge {fmt_prob(no)} >= {fmt_prob(min_edge)}"
    if max(abs(yes), abs(no)) <= Decimal("0.03"):
        return "NONE", "FAIR_ALIGNED", "proxy fair value close to market"
    return "NONE", "MODEL_WATCH", "proxy divergence below promotion threshold"


def parse_target_date(question: str, end_date: datetime | None) -> date | None:
    match = re.search(r"\bon\s+([A-Za-z]+)\s+(\d{1,2})(?:,\s*(\d{4}))?", question)
    if not match:
        return end_date.date() if isinstance(end_date, datetime) else None
    month = MONTHS.get(match.group(1).lower())
    if not month:
        return None
    year = int(match.group(3)) if match.group(3) else (end_date.year if isinstance(end_date, datetime) else datetime.now(UTC).year)
    return date(year, month, int(match.group(2)))


def parse_threshold(text: str) -> tuple[str, Decimal, Decimal] | None:
    clean = text.replace("º", "").replace("°", "").strip()
    between = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*([CF])", clean, re.IGNORECASE)
    if between:
        low = Decimal(between.group(1)) - Decimal("0.5")
        high = Decimal(between.group(2)) + Decimal("0.5")
        unit = between.group(3).upper()
        return "between", temp_to_c(low, unit), temp_to_c(high, unit)
    single = re.search(r"(\d+(?:\.\d+)?)\s*([CF])", clean, re.IGNORECASE)
    if not single:
        return None
    value = Decimal(single.group(1))
    unit = single.group(2).upper()
    lower_text = clean.lower()
    if "or higher" in lower_text:
        return "or_higher", temp_to_c(value - Decimal("0.5"), unit), Decimal("999")
    if "or lower" in lower_text or "or below" in lower_text:
        return "or_lower", Decimal("-999"), temp_to_c(value + Decimal("0.5"), unit)
    return "exact", temp_to_c(value - Decimal("0.5"), unit), temp_to_c(value + Decimal("0.5"), unit)


def interval_probability(mean: Decimal, sigma: Decimal, low: Decimal, high: Decimal) -> Decimal:
    mean_f = float(mean)
    sigma_f = max(0.1, float(sigma))
    low_f = float(low)
    high_f = float(high)
    prob = normal_cdf((high_f - mean_f) / sigma_f) - normal_cdf((low_f - mean_f) / sigma_f)
    return Decimal(str(max(0.0, min(1.0, prob)))).quantize(Decimal("0.000001"))


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def sigma_for(target_date: date, observed_at: datetime) -> Decimal:
    days = (target_date - observed_at.date()).days
    if days <= 0:
        return Decimal("1.20")
    if days <= 2:
        return Decimal("1.60")
    if days <= 5:
        return Decimal("2.20")
    return Decimal("3.00")


def temp_to_c(value: Decimal, unit: str) -> Decimal:
    if unit.upper() == "F":
        return (value - Decimal("32")) * Decimal("5") / Decimal("9")
    return value


async def persist_edges(conn: asyncpg.Connection, edges: list[ForecastEdge]) -> None:
    for edge in edges:
        await conn.execute(
            """
            INSERT INTO app.weather_forecast_edges (
                scan_id, observed_at, radar_tick_id, condition_id, question,
                location_hint, target_date, threshold_hint, forecast_max_c, model_sigma_c,
                fair_yes, market_mid, best_yes_bid, best_yes_ask, best_no_ask, spread,
                edge_yes, edge_no, action_bias, model_state, reason, source_url, raw
            )
            VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16,
                $17, $18, $19, $20, $21, $22, $23::jsonb
            )
            """,
            edge.scan_id,
            edge.observed_at,
            edge.radar_tick_id,
            edge.condition_id,
            edge.question,
            edge.location_hint,
            edge.target_date,
            edge.threshold_hint,
            edge.forecast_max_c,
            edge.model_sigma_c,
            edge.fair_yes,
            edge.market_mid,
            edge.best_yes_bid,
            edge.best_yes_ask,
            edge.best_no_ask,
            edge.spread,
            edge.edge_yes,
            edge.edge_no,
            edge.action_bias,
            edge.model_state,
            edge.reason,
            edge.source_url,
            json.dumps({**edge.raw, "source_adapter": edge.source_adapter}, default=str),
        )


def render_report(edges: list[ForecastEdge], *, min_edge: Decimal, max_spread: Decimal) -> str:
    counts: dict[str, int] = {}
    for edge in edges:
        counts[edge.model_state] = counts.get(edge.model_state, 0) + 1
    return f"""{render_frontmatter({"type": "weather-forecast-edge-scores", "tags": ["research", "weather", "edge", "paper-only"]})}
# Weather Forecast Edge Scores

Generated at: `{datetime.now(UTC).isoformat()}`

Mode: `research_read_only`. Source: `open-meteo-proxy`.

Important: this is a proxy model, not a production trading signal. Before live use, verify the exact Polymarket resolution source and replay forecast timestamp changes against orderbook movement.

Promotion filters:
- Minimum proxy edge: `{min_edge}`
- Maximum spread: `{max_spread}`

## State Counts
{bullets([f"{key}: {value}" for key, value in sorted(counts.items())])}

## Top Scores
{render_edges_table(sorted(edges, key=edge_sort_key)[:20])}
"""


def render_edges_table(edges: list[ForecastEdge]) -> str:
    if not edges:
        return "No scored edges."
    lines = [
        "| State | Bias | Fair Yes | Mid | Edge Yes | Edge No | Forecast C | Market | Reason |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for edge in edges:
        lines.append(
            f"| {edge.model_state} | {edge.action_bias} | {fmt_prob(edge.fair_yes)} | "
            f"{fmt_prob(edge.market_mid)} | {fmt_prob(edge.edge_yes)} | {fmt_prob(edge.edge_no)} | "
            f"{fmt_prob(edge.forecast_max_c)} | {edge.question[:68]} | {edge.reason} |"
        )
    return "\n".join(lines)


def edge_sort_key(edge: ForecastEdge) -> tuple[int, Decimal]:
    rank = {"EDGE_CANDIDATE": 0, "MODEL_WATCH": 1, "FAIR_ALIGNED": 2, "SPREAD_BLOCKED": 3, "MODEL_BLOCKED": 4}
    best_edge = max(edge.edge_yes or Decimal("-99"), edge.edge_no or Decimal("-99"))
    return rank.get(edge.model_state, 9), -best_edge


def edge_to_json(edge: ForecastEdge) -> dict[str, Any]:
    return json.loads(json.dumps(asdict(edge), default=str))


def extract_resolution_source(row: asyncpg.Record) -> dict[str, str]:
    raw = row["raw"] or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = {}
    market = raw.get("market") if isinstance(raw, dict) else {}
    description = str((market or {}).get("description") or "")
    url_match = re.search(r"https?://[^\s)]+", description)
    url = url_match.group(0).rstrip(".") if url_match else ""
    lowered = description.lower()
    if "wunderground.com" in lowered:
        return {"kind": "wunderground", "url": url}
    if "hong kong observatory" in lowered or "weather.gov.hk" in lowered:
        return {"kind": "hko", "url": url}
    return {"kind": "unknown", "url": url}


def station_from_source(source: dict[str, str]) -> str | None:
    if source.get("kind") != "wunderground":
        return None
    url = source.get("url") or ""
    match = re.search(r"/([A-Z]{4})(?:[/?#.]|$)", url)
    return match.group(1) if match else None


def to_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def fmt_prob(value: Any) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{Decimal(str(value)):.4f}"
    except InvalidOperation:
        return str(value)


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
