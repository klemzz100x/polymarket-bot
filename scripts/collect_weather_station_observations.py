#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import asyncpg
import httpx

from polybot.core.config import get_settings
from polybot.knowledge.obsidian import ObsidianVault
from polybot.resources.markdown import render_frontmatter


DEFAULT_STATIONS = ("EGLC", "KAUS", "RKSI")


CREATE_OBSERVATIONS_TABLE_SQL = """
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.weather_station_observations (
    id BIGSERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    station_id TEXT NOT NULL,
    station_name TEXT,
    report_time TIMESTAMPTZ,
    obs_time TIMESTAMPTZ,
    temp_c NUMERIC(10, 4),
    dewpoint_c NUMERIC(10, 4),
    wind_dir INTEGER,
    wind_speed INTEGER,
    source_name TEXT NOT NULL DEFAULT 'aviationweather.gov-metar',
    source_url TEXT NOT NULL DEFAULT '',
    raw_metar TEXT NOT NULL DEFAULT '',
    raw JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (station_id, report_time, raw_metar)
);

CREATE INDEX IF NOT EXISTS ix_weather_station_observations_collected
    ON app.weather_station_observations(collected_at DESC);

CREATE INDEX IF NOT EXISTS ix_weather_station_observations_station_report
    ON app.weather_station_observations(station_id, report_time DESC);
"""


@dataclass(slots=True)
class StationObservation:
    batch_id: str
    collected_at: datetime
    station_id: str
    station_name: str | None
    report_time: datetime | None
    obs_time: datetime | None
    temp_c: Decimal | None
    dewpoint_c: Decimal | None
    wind_dir: int | None
    wind_speed: int | None
    source_url: str
    raw_metar: str
    raw: dict[str, Any]


async def main_async() -> int:
    parser = argparse.ArgumentParser(
        description="Collect read-only METAR station observations for weather-market validation."
    )
    parser.add_argument("--stations", default=",".join(DEFAULT_STATIONS), help="Comma-separated ICAO station ids.")
    parser.add_argument("--no-db", action="store_true")
    parser.add_argument("--json-out", type=Path, default=Path("resources/edge-tests/weather_station_observations.json"))
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    parser.add_argument("--obsidian", action="store_true")
    args = parser.parse_args()

    station_ids = [item.strip().upper() for item in args.stations.split(",") if item.strip()]
    batch_id = f"weather-metar-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
    collected_at = datetime.now(UTC)
    observations = await fetch_observations(batch_id, collected_at, station_ids)

    payload = {
        "batch_id": batch_id,
        "generated_at": collected_at.isoformat(),
        "mode": "research_read_only",
        "live_trading": "disabled",
        "source": "aviationweather.gov-metar",
        "warning": "METAR is station observation evidence, not an order signal.",
        "observations": [observation_to_json(item) for item in observations],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    if not args.no_db:
        settings = get_settings()
        conn = await asyncpg.connect(resolve_database_url(settings.database_url))
        try:
            await conn.execute(CREATE_OBSERVATIONS_TABLE_SQL)
            await persist_observations(conn, observations)
        finally:
            await conn.close()

    report_path = None
    if args.obsidian:
        vault = ObsidianVault(args.vault)
        vault.ensure_structure()
        report_path = vault.write_note(
            "Research/Edge-Research",
            "Weather Station Observations",
            render_report(observations),
            overwrite=True,
        )

    print(f"Weather station observations batch={batch_id} count={len(observations)}")
    print(f"JSON={args.json_out}")
    if report_path:
        print(f"Report={report_path}")
    for item in observations:
        print(
            f"- {item.station_id} {fmt_decimal(item.temp_c)}C report={item.report_time.isoformat() if item.report_time else 'n/a'}"
        )
    return 0


async def fetch_observations(
    batch_id: str,
    collected_at: datetime,
    station_ids: list[str],
) -> list[StationObservation]:
    if not station_ids:
        return []
    source_url = "https://aviationweather.gov/api/data/metar"
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.get(
            source_url,
            params={"ids": ",".join(station_ids), "format": "json", "taf": "false"},
        )
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, list):
        return []
    return [observation_from_payload(batch_id, collected_at, source_url, item) for item in payload if isinstance(item, dict)]


def observation_from_payload(
    batch_id: str,
    collected_at: datetime,
    source_url: str,
    payload: dict[str, Any],
) -> StationObservation:
    return StationObservation(
        batch_id=batch_id,
        collected_at=collected_at,
        station_id=str(payload.get("icaoId") or "").upper(),
        station_name=str(payload.get("name")) if payload.get("name") is not None else None,
        report_time=parse_datetime(payload.get("reportTime")),
        obs_time=parse_obs_time(payload.get("obsTime")),
        temp_c=to_decimal(payload.get("temp")),
        dewpoint_c=to_decimal(payload.get("dewp")),
        wind_dir=to_int(payload.get("wdir")),
        wind_speed=to_int(payload.get("wspd")),
        source_url=source_url,
        raw_metar=str(payload.get("rawOb") or ""),
        raw=payload,
    )


async def persist_observations(conn: asyncpg.Connection, observations: list[StationObservation]) -> None:
    for item in observations:
        await conn.execute(
            """
            INSERT INTO app.weather_station_observations (
                batch_id, collected_at, station_id, station_name, report_time, obs_time,
                temp_c, dewpoint_c, wind_dir, wind_speed, source_url, raw_metar, raw
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::jsonb)
            ON CONFLICT (station_id, report_time, raw_metar) DO UPDATE SET
                batch_id = EXCLUDED.batch_id,
                collected_at = EXCLUDED.collected_at,
                temp_c = EXCLUDED.temp_c,
                dewpoint_c = EXCLUDED.dewpoint_c,
                wind_dir = EXCLUDED.wind_dir,
                wind_speed = EXCLUDED.wind_speed,
                raw = EXCLUDED.raw
            """,
            item.batch_id,
            item.collected_at,
            item.station_id,
            item.station_name,
            item.report_time,
            item.obs_time,
            item.temp_c,
            item.dewpoint_c,
            item.wind_dir,
            item.wind_speed,
            item.source_url,
            item.raw_metar,
            json.dumps(item.raw, default=str),
        )


def render_report(observations: list[StationObservation]) -> str:
    return f"""{render_frontmatter({"type": "weather-station-observations", "tags": ["research", "weather", "metar", "paper-only"]})}
# Weather Station Observations

Generated at: `{datetime.now(UTC).isoformat()}`

Mode: `research_read_only`. Source: `aviationweather.gov-metar`.

These observations are evidence for weather-market validation. They do not enable trading and should not be treated as an order signal by themselves.

## Latest Station Reads
{render_table(observations)}
"""


def render_table(observations: list[StationObservation]) -> str:
    if not observations:
        return "No station observations collected."
    lines = [
        "| Station | Temp C | Report Time | Wind | Raw METAR |",
        "|---|---:|---|---:|---|",
    ]
    for item in observations:
        lines.append(
            f"| {item.station_id} | {fmt_decimal(item.temp_c)} | "
            f"{item.report_time.isoformat() if item.report_time else 'n/a'} | "
            f"{item.wind_speed if item.wind_speed is not None else 'n/a'} | {item.raw_metar[:90]} |"
        )
    return "\n".join(lines)


def observation_to_json(observation: StationObservation) -> dict[str, Any]:
    return json.loads(json.dumps(asdict(observation), default=str))


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def parse_obs_time(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=UTC)
    except (TypeError, ValueError, OSError):
        return None


def to_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def fmt_decimal(value: Decimal | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


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
