#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import asyncpg

from polybot.core.config import get_settings
from polybot.knowledge.obsidian import ObsidianVault
from polybot.resources.markdown import render_frontmatter


CREATE_GATE_TABLE_SQL = """
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.weather_live_gate_reports (
    id BIGSERIAL PRIMARY KEY,
    report_id TEXT NOT NULL UNIQUE,
    generated_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    score NUMERIC(10, 4) NOT NULL,
    checks JSONB NOT NULL,
    blockers JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_weather_live_gate_reports_generated
    ON app.weather_live_gate_reports(generated_at DESC);
CREATE INDEX IF NOT EXISTS ix_weather_live_gate_reports_status
    ON app.weather_live_gate_reports(status, generated_at DESC);
"""


@dataclass(slots=True)
class GateCheck:
    name: str
    status: str
    value: str
    required: str
    blocker: bool


@dataclass(slots=True)
class GateReport:
    report_id: str
    generated_at: datetime
    status: str
    score: Decimal
    checks: list[GateCheck]
    blockers: list[str]
    recommendations: list[str]


async def main_async() -> int:
    parser = argparse.ArgumentParser(description="Weather strategy live go/no-go gate. Does not enable live trading.")
    parser.add_argument("--json-out", type=Path, default=Path("resources/edge-tests/weather_live_go_no_go.json"))
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    parser.add_argument("--persist-db", action="store_true")
    parser.add_argument("--obsidian", action="store_true")
    parser.add_argument("--min-scans", type=int, default=12)
    parser.add_argument("--min-exact-edge-candidates", type=int, default=1)
    parser.add_argument("--min-stable-hours", type=int, default=6)
    args = parser.parse_args()

    settings = get_settings()
    conn = await asyncpg.connect(resolve_database_url(settings.database_url))
    try:
        report = await build_report(conn, settings, args)
        if args.persist_db:
            await conn.execute(CREATE_GATE_TABLE_SQL)
            await persist_report(conn, report)
    finally:
        await conn.close()

    payload = report_to_json(report)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    report_path = None
    if args.obsidian:
        vault = ObsidianVault(args.vault)
        vault.ensure_structure()
        report_path = vault.write_note(
            "Live-Readiness",
            "Weather Live Go No-Go",
            render_report(report),
            overwrite=True,
        )

    print(f"Weather live gate status={report.status} score={report.score}")
    print(f"JSON={args.json_out}")
    if report_path:
        print(f"Report={report_path}")
    for check in report.checks:
        print(f"- {check.status}: {check.name} value={check.value} required={check.required}")
    if report.blockers:
        print("Blockers:")
        for blocker in report.blockers:
            print(f"- {blocker}")
    return 0 if report.status != "ERROR" else 1


async def build_report(conn: asyncpg.Connection, settings: Any, args: argparse.Namespace) -> GateReport:
    generated_at = datetime.now(UTC)
    checks: list[GateCheck] = []

    live_enabled = str(settings.live_trading_enabled).lower()
    checks.append(
        GateCheck(
            "live_trading_still_disabled",
            "PASS" if not settings.live_trading_enabled else "FAIL",
            live_enabled,
            "false during readiness",
            True,
        )
    )
    mode = str(settings.live_execution_mode).upper()
    checks.append(
        GateCheck(
            "live_execution_mode_disabled",
            "PASS" if mode == "DISABLED" else "FAIL",
            mode,
            "DISABLED during readiness",
            True,
        )
    )
    checks.append(
        GateCheck(
            "no_private_key_loaded_in_readiness",
            "PASS" if not settings.polymarket_private_key else "FAIL",
            "empty" if not settings.polymarket_private_key else "present",
            "empty until explicit live cutover",
            True,
        )
    )

    scan_count = await scalar_int(
        conn,
        """
        SELECT COUNT(DISTINCT scan_id)
        FROM app.weather_market_radar_ticks
        WHERE observed_at > now() - interval '24 hours'
        """,
    )
    checks.append(
        GateCheck(
            "weather_scan_sample_size_24h",
            "PASS" if scan_count >= args.min_scans else "FAIL",
            str(scan_count),
            f">= {args.min_scans}",
            True,
        )
    )

    stable_hours = await scalar_decimal(
        conn,
        """
        SELECT COALESCE(EXTRACT(EPOCH FROM (MAX(observed_at) - MIN(observed_at))) / 3600, 0)
        FROM app.weather_forecast_edges
        WHERE observed_at > now() - interval '24 hours'
          AND model_state = 'EDGE_CANDIDATE'
        """,
    )
    checks.append(
        GateCheck(
            "edge_stability_window",
            "PASS" if stable_hours >= Decimal(args.min_stable_hours) else "FAIL",
            f"{stable_hours:.2f}h",
            f">= {args.min_stable_hours}h",
            True,
        )
    )

    exact_edges = await scalar_int(
        conn,
        """
        SELECT COUNT(*)
        FROM app.weather_forecast_edges
        WHERE observed_at > now() - interval '24 hours'
          AND model_state = 'EDGE_CANDIDATE'
          AND raw->>'source_adapter' LIKE 'open-meteo-resolution-station-proxy:%'
        """,
    )
    checks.append(
        GateCheck(
            "exact_station_proxy_edge_candidates",
            "PASS" if exact_edges >= args.min_exact_edge_candidates else "FAIL",
            str(exact_edges),
            f">= {args.min_exact_edge_candidates}",
            True,
        )
    )

    hko_blocked = await scalar_int(
        conn,
        """
        SELECT COUNT(*)
        FROM app.weather_forecast_edges
        WHERE observed_at > now() - interval '24 hours'
          AND raw->>'source_adapter' LIKE '%hko-resolution-mismatch%'
        """,
    )
    checks.append(
        GateCheck(
            "hko_source_adapter",
            "PASS" if hko_blocked == 0 else "FAIL",
            str(hko_blocked),
            "0 unresolved HKO candidates",
            False,
        )
    )

    station_observations = await scalar_int(
        conn,
        """
        SELECT CASE
            WHEN to_regclass('app.weather_station_observations') IS NULL THEN 0
            ELSE (
                SELECT COUNT(DISTINCT station_id)
                FROM app.weather_station_observations
                WHERE collected_at > now() - interval '2 hours'
                  AND temp_c IS NOT NULL
            )
        END
        """,
    )
    checks.append(
        GateCheck(
            "fresh_station_observations",
            "PASS" if station_observations >= 1 else "FAIL",
            str(station_observations),
            ">= 1 station with temp in last 2h",
            True,
        )
    )

    recent_readiness = await conn.fetchrow(
        """
        SELECT status, live_readiness_score, kill_switch_state, generated_at
        FROM app.live_readiness_reports
        ORDER BY generated_at DESC
        LIMIT 1
        """
    )
    readiness_ok = bool(
        recent_readiness
        and str(recent_readiness["status"]).lower() in {"ready", "pass"}
        and Decimal(str(recent_readiness["live_readiness_score"] or 0)) >= Decimal("0.80")
    )
    checks.append(
        GateCheck(
            "generic_live_readiness_report",
            "PASS" if readiness_ok else "FAIL",
            f"{recent_readiness['status']} {recent_readiness['live_readiness_score']}"
            if recent_readiness
            else "missing",
            "ready/pass and score >= 0.80",
            True,
        )
    )

    blockers = [
        f"{check.name}: value {check.value}, required {check.required}"
        for check in checks
        if check.blocker and check.status != "PASS"
    ]
    warnings = [
        f"{check.name}: value {check.value}, required {check.required}"
        for check in checks
        if not check.blocker and check.status != "PASS"
    ]
    passed = sum(1 for check in checks if check.status == "PASS")
    score = (Decimal(passed) / Decimal(len(checks))).quantize(Decimal("0.0001"))
    if blockers:
        status = "NO_GO"
    elif warnings:
        status = "PAPER_READY_WITH_WARNINGS"
    else:
        status = "MICRO_LIVE_READY"

    recommendations = [
        "Do not paste or store seed phrases in chat, repo, dashboard, or .env.",
        "Use a fresh dedicated Polymarket wallet with tiny capital only.",
        "Keep first live cutover at micro-size and maker/limit-only until fill behavior is observed.",
        "Before changing env flags, run this gate again and archive the report.",
    ]
    if blockers:
        recommendations.insert(0, "Keep LIVE_TRADING_ENABLED=false and LIVE_EXECUTION_MODE=DISABLED.")
    if warnings:
        recommendations.append("Resolve non-blocking warnings before scaling beyond micro-live.")
    return GateReport(
        report_id=str(uuid4()),
        generated_at=generated_at,
        status=status,
        score=score,
        checks=checks,
        blockers=blockers,
        recommendations=recommendations,
    )


async def persist_report(conn: asyncpg.Connection, report: GateReport) -> None:
    await conn.execute(
        """
        INSERT INTO app.weather_live_gate_reports (
            report_id, generated_at, status, score, checks, blockers, recommendations
        )
        VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7::jsonb)
        ON CONFLICT (report_id) DO NOTHING
        """,
        report.report_id,
        report.generated_at,
        report.status,
        report.score,
        json.dumps([asdict(check) for check in report.checks], default=str),
        json.dumps(report.blockers),
        json.dumps(report.recommendations),
    )


def render_report(report: GateReport) -> str:
    return f"""{render_frontmatter({"type": "weather-live-go-no-go", "tags": ["live-readiness", "weather", "safety"]})}
# Weather Live Go/No-Go

Generated at: `{report.generated_at.isoformat()}`

Status: `{report.status}`

Score: `{report.score}`

## Checks
{render_checks(report.checks)}

## Blockers
{bullets(report.blockers or ["No blocking gate failed."])}

## Recommendations
{bullets(report.recommendations)}
"""


def render_checks(checks: list[GateCheck]) -> str:
    lines = ["| Status | Check | Value | Required | Blocker |", "|---|---|---|---|---|"]
    for check in checks:
        lines.append(f"| {check.status} | {check.name} | {check.value} | {check.required} | {check.blocker} |")
    return "\n".join(lines)


def report_to_json(report: GateReport) -> dict[str, Any]:
    return {
        "report_id": report.report_id,
        "generated_at": report.generated_at.isoformat(),
        "status": report.status,
        "score": str(report.score),
        "checks": [asdict(check) for check in report.checks],
        "blockers": report.blockers,
        "recommendations": report.recommendations,
    }


async def scalar_int(conn: asyncpg.Connection, query: str) -> int:
    return int(await conn.fetchval(query) or 0)


async def scalar_decimal(conn: asyncpg.Connection, query: str) -> Decimal:
    return Decimal(str(await conn.fetchval(query) or 0))


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
