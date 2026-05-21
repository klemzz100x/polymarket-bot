#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
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


async def main_async() -> int:
    parser = argparse.ArgumentParser(description="Verify Polymarket resolution rules for weather edge candidates.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json-out", type=Path, default=Path("resources/edge-tests/weather_resolution_rules.json"))
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    parser.add_argument("--obsidian", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    conn = await asyncpg.connect(resolve_database_url(settings.database_url))
    try:
        rows = await conn.fetch(
            """
            SELECT DISTINCT ON (r.event_slug, e.condition_id)
                   e.model_state, e.action_bias, e.fair_yes, e.market_mid, e.edge_yes, e.edge_no,
                   r.event_slug, r.market_slug, r.condition_id, r.question, r.source_url
            FROM app.weather_forecast_edges e
            JOIN app.weather_market_radar_ticks r ON r.id = e.radar_tick_id
            WHERE e.model_state IN ('EDGE_CANDIDATE', 'MODEL_WATCH', 'FAIR_ALIGNED')
            ORDER BY r.event_slug, e.condition_id, e.observed_at DESC
            LIMIT $1
            """,
            args.limit,
        )
    finally:
        await conn.close()

    records = await fetch_rule_records(settings, rows)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": "research_read_only",
        "live_trading": "disabled",
        "records": records,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    report_path = None
    if args.obsidian:
        vault = ObsidianVault(args.vault)
        vault.ensure_structure()
        report_path = vault.write_note(
            "Research/Edge-Research",
            "Weather Resolution Rule Audit",
            render_report(records),
            overwrite=True,
        )

    counts: dict[str, int] = {}
    for record in records:
        counts[record["rule_state"]] = counts.get(record["rule_state"], 0) + 1
    print(f"Weather rule audit records={len(records)} states={counts}")
    print(f"JSON={args.json_out}")
    if report_path:
        print(f"Report={report_path}")
    for record in records[:10]:
        print(f"- {record['rule_state']}: {record['question'][:84]} | {record['primary_resolution_source']}")
    return 0


async def fetch_rule_records(settings: Any, rows: list[asyncpg.Record]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=25) as client:
        for row in rows:
            event_slug = row["event_slug"]
            event_payload: dict[str, Any] = {}
            if event_slug:
                response = await client.get(f"{settings.polymarket_gamma_api_url}/events/slug/{event_slug}")
                if response.status_code == 200:
                    event_payload = response.json()
            market_payload = find_market_payload(event_payload, row["condition_id"])
            description = str(market_payload.get("description") or event_payload.get("description") or "")
            resolution_source = str(market_payload.get("resolutionSource") or event_payload.get("resolutionSource") or "")
            source_summary = summarize_resolution_source(description, resolution_source)
            rule_state = classify_rule_state(source_summary)
            records.append(
                {
                    "model_state": row["model_state"],
                    "action_bias": row["action_bias"],
                    "fair_yes": str(row["fair_yes"]),
                    "market_mid": str(row["market_mid"]),
                    "edge_yes": str(row["edge_yes"]),
                    "edge_no": str(row["edge_no"]),
                    "condition_id": row["condition_id"],
                    "event_slug": event_slug,
                    "market_slug": row["market_slug"],
                    "question": row["question"],
                    "source_url": row["source_url"],
                    "rule_state": rule_state,
                    "primary_resolution_source": source_summary["primary_source"],
                    "temperature_location_rule": source_summary["location_rule"],
                    "measurement_rule": source_summary["measurement_rule"],
                    "risk_notes": source_summary["risk_notes"],
                    "description_excerpt": description[:1400],
                    "resolution_source_field": resolution_source,
                }
            )
    records.sort(key=lambda item: (state_rank(item["rule_state"]), item["question"]))
    return records


def find_market_payload(event_payload: dict[str, Any], condition_id: str | None) -> dict[str, Any]:
    for market in event_payload.get("markets") or []:
        if not isinstance(market, dict):
            continue
        if market.get("conditionId") == condition_id:
            return market
    markets = event_payload.get("markets") or []
    return markets[0] if markets and isinstance(markets[0], dict) else {}


def summarize_resolution_source(description: str, resolution_source: str) -> dict[str, Any]:
    text = " ".join(description.split())
    lowered = text.lower()
    urls = re.findall(r"https?://[^\s)]+", description)
    primary_source = resolution_source.strip() or first_matching_sentence(text, ("primary resolution source", "resolution source"))
    if not primary_source and urls:
        primary_source = urls[0]
    if not primary_source:
        primary_source = "not explicitly found"

    location_rule = first_matching_sentence(
        text,
        ("weather station", "station", "airport", "city", "temperature in"),
    )
    measurement_rule = first_matching_sentence(
        text,
        ("highest temperature", "maximum temperature", "temperature will be", "resolve to"),
    )
    risk_notes: list[str] = []
    if "accuweather" in lowered:
        risk_notes.append("mentions AccuWeather; Open-Meteo is only a proxy")
    if "weather.com" in lowered or "weather underground" in lowered:
        risk_notes.append("mentions a non Open-Meteo source; source mismatch must be replayed")
    if "consensus" in lowered:
        risk_notes.append("fallback may use consensus reporting")
    if not urls and "not explicitly found" in primary_source:
        risk_notes.append("no explicit URL detected in description excerpt")
    if not location_rule:
        risk_notes.append("location/station rule not extracted")
    if not measurement_rule:
        risk_notes.append("measurement rule not extracted")
    return {
        "primary_source": primary_source[:500],
        "location_rule": location_rule[:500] if location_rule else "",
        "measurement_rule": measurement_rule[:500] if measurement_rule else "",
        "urls": urls,
        "risk_notes": risk_notes,
    }


def classify_rule_state(source_summary: dict[str, Any]) -> str:
    risk_notes = source_summary["risk_notes"]
    primary = str(source_summary["primary_source"]).lower()
    if "not explicitly found" in primary:
        return "RULE_SOURCE_MISSING"
    if any("proxy" in note.lower() or "mismatch" in note.lower() for note in risk_notes):
        return "SOURCE_MISMATCH_RISK"
    if source_summary["location_rule"] and source_summary["measurement_rule"]:
        return "RULES_EXTRACTED"
    return "RULES_PARTIAL"


def first_matching_sentence(text: str, needles: tuple[str, ...]) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentences:
        lower = sentence.lower()
        if any(needle in lower for needle in needles):
            return sentence.strip()
    return ""


def render_report(records: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for record in records:
        counts[record["rule_state"]] = counts.get(record["rule_state"], 0) + 1
    return f"""{render_frontmatter({"type": "weather-resolution-rule-audit", "tags": ["research", "weather", "rules", "paper-only"]})}
# Weather Resolution Rule Audit

Generated at: `{datetime.now(UTC).isoformat()}`

Mode: `research_read_only`. This audit checks whether proxy forecast edges are aligned with Polymarket resolution language.

## Verdict
- `RULES_EXTRACTED` means the market text contains enough source/rule detail to design a replay.
- `SOURCE_MISMATCH_RISK` means the proxy may disagree with the resolution source. Do not promote these to live until replayed against the exact source.
- `RULE_SOURCE_MISSING` means no live consideration.

## State Counts
{bullets([f"{key}: {value}" for key, value in sorted(counts.items())])}

## Candidate Rules
{render_records_table(records)}
"""


def render_records_table(records: list[dict[str, Any]]) -> str:
    if not records:
        return "No records."
    lines = [
        "| Rule State | Bias | Market | Primary Source | Risk Notes |",
        "|---|---|---|---|---|",
    ]
    for record in records:
        lines.append(
            f"| {record['rule_state']} | {record['action_bias']} | {record['question'][:72]} | "
            f"{str(record['primary_resolution_source'])[:96]} | {', '.join(record['risk_notes'])[:120]} |"
        )
    return "\n".join(lines)


def state_rank(state: str) -> int:
    return {
        "RULES_EXTRACTED": 0,
        "RULES_PARTIAL": 1,
        "SOURCE_MISMATCH_RISK": 2,
        "RULE_SOURCE_MISSING": 3,
    }.get(state, 9)


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
