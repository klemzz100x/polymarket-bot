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

import asyncpg

from polybot.knowledge.obsidian import ObsidianVault
from polybot.resources.markdown import render_frontmatter


@dataclass(frozen=True, slots=True)
class EdgeTestResult:
    family: str
    status: str
    hypothesis: str
    candidate_markets: int
    covered_markets: int
    snapshots: int
    verdict: str
    next_action: str
    blockers: list[str]
    sample_markets: list[dict[str, Any]]


EDGE_TESTS = {
    "weather_event_discovery": {
        "hypothesis": "Forecast updates can identify weather markets that reprice slower than external weather feeds.",
        "patterns": (
            r"\mweather\M",
            r"\mtemperature\M",
            r"\mrain\M",
            r"\msnow\M",
            r"\mstorm\M",
            r"\mwind\M",
            r"\mheat\M",
            r"hurricane (landfall|season|category)",
        ),
        "minimum_snapshots": 100,
        "next_action": "Collect weather-specific markets plus timestamped forecast snapshots before replay testing.",
    },
    "crypto_5m_microstructure": {
        "hypothesis": "CEX BTC/ETH microstructure can lead Polymarket short-window crypto markets after latency and spread.",
        "patterns": (
            r"\mbtc\M",
            r"\mbitcoin\M",
            r"\meth\M",
            r"\methereum\M",
            r"\mcrypto\M",
            r"5[- ]minute",
            r"up/down",
        ),
        "minimum_snapshots": 300,
        "next_action": "Collect short-window crypto markets with second-level CEX reference prices and dense orderbooks.",
    },
    "news_latency": {
        "hypothesis": "Credible news events can move real-world probabilities before Polymarket fully reprices.",
        "patterns": (
            r"\mnews\M",
            r"\mfed\M",
            r"\melection\M",
            r"\mtariff\M",
            r"rate cut",
            r"\mnomination\M",
            r"\mwar\M",
            r"\mceasefire\M",
        ),
        "minimum_snapshots": 100,
        "next_action": "Build an external event timestamp feed and map events to market condition_ids before replay.",
    },
}


async def main_async() -> int:
    parser = argparse.ArgumentParser(description="Run read-only research readiness tests for extracted edge families.")
    parser.add_argument("--json-out", type=Path, default=Path("resources/edge-tests/edge_research_tests.json"))
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    args = parser.parse_args()

    database_url = normalize_database_url(
        os.getenv("DATABASE_URL", "postgresql://polymarket:change-me@postgres:5432/polymarket")
    )
    conn = await asyncpg.connect(database_url)
    try:
        results = [await run_family_test(conn, family, config) for family, config in EDGE_TESTS.items()]
    finally:
        await conn.close()

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": "research_readiness_only",
        "live_trading": "disabled",
        "results": [asdict(result) for result in results],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=json_default), encoding="utf-8")

    vault = ObsidianVault(args.vault)
    vault.ensure_structure()
    report_path = vault.write_note(
        "Research/Edge-Research",
        "Edge Research Test Results",
        render_report(results),
        overwrite=True,
    )

    print(f"Generated {len(results)} edge research tests.")
    print(f"JSON={args.json_out}")
    print(f"Report={report_path}")
    for result in results:
        print(
            f"- {result.family}: {result.status} "
            f"candidates={result.candidate_markets} covered={result.covered_markets} snapshots={result.snapshots}"
        )
    return 0


async def run_family_test(conn: asyncpg.Connection, family: str, config: dict[str, Any]) -> EdgeTestResult:
    patterns = tuple(config["patterns"])
    markets = await conn.fetch(
        """
        SELECT condition_id, question, category, active, closed, volume, liquidity, end_date
        FROM app.markets
        WHERE condition_id IS NOT NULL
          AND EXISTS (
            SELECT 1
            FROM unnest($1::text[]) AS pattern
            WHERE question ~* pattern
               OR coalesce(category, '') ~* pattern
               OR coalesce(slug, '') ~* pattern
          )
        ORDER BY active DESC, volume DESC NULLS LAST, liquidity DESC NULLS LAST
        LIMIT 25
        """,
        list(patterns),
    )
    condition_ids = [row["condition_id"] for row in markets]
    coverage = []
    if condition_ids:
        coverage = await conn.fetch(
            """
            WITH best_levels AS (
                SELECT s.condition_id, s.id, s.snapshot_ts,
                       MAX(CASE WHEN l.side = 'bid' THEN l.price END) AS best_bid,
                       MIN(CASE WHEN l.side = 'ask' THEN l.price END) AS best_ask
                FROM app.orderbook_snapshots s
                LEFT JOIN app.orderbook_levels l ON l.snapshot_id = s.id
                WHERE s.condition_id = ANY($1::text[])
                GROUP BY s.condition_id, s.id, s.snapshot_ts
            )
            SELECT condition_id,
                   COUNT(*) AS snapshots,
                   MIN(snapshot_ts) AS first_snapshot,
                   MAX(snapshot_ts) AS last_snapshot,
                   AVG(best_ask - best_bid) FILTER (WHERE best_bid IS NOT NULL AND best_ask IS NOT NULL) AS avg_spread
            FROM best_levels
            GROUP BY condition_id
            ORDER BY snapshots DESC
            """,
            condition_ids,
        )
    coverage_by_market = {row["condition_id"]: row for row in coverage}
    snapshots = sum(int(row["snapshots"] or 0) for row in coverage)
    covered_markets = sum(1 for row in coverage if int(row["snapshots"] or 0) > 0)
    blockers = blockers_for(config, len(markets), covered_markets, snapshots)
    status = "ready_for_replay" if not blockers else "needs_data"
    sample_markets = [market_row(row, coverage_by_market.get(row["condition_id"])) for row in markets[:8]]
    verdict = verdict_for(status, family, snapshots, int(config["minimum_snapshots"]))
    return EdgeTestResult(
        family=family,
        status=status,
        hypothesis=str(config["hypothesis"]),
        candidate_markets=len(markets),
        covered_markets=covered_markets,
        snapshots=snapshots,
        verdict=verdict,
        next_action=str(config["next_action"]),
        blockers=blockers,
        sample_markets=sample_markets,
    )


def blockers_for(config: dict[str, Any], candidate_markets: int, covered_markets: int, snapshots: int) -> list[str]:
    blockers: list[str] = []
    if candidate_markets == 0:
        blockers.append("No matching markets found in app.markets for this edge family.")
    if covered_markets == 0:
        blockers.append("No matching markets currently have stored orderbook snapshots.")
    if snapshots < int(config["minimum_snapshots"]):
        blockers.append(
            f"Only {snapshots} snapshots available; minimum for a first replay is {config['minimum_snapshots']}."
        )
    return blockers


def verdict_for(status: str, family: str, snapshots: int, minimum_snapshots: int) -> str:
    if status == "ready_for_replay":
        return "Enough local data exists for a first replay-style paper research test."
    return (
        f"{family} is a valid hypothesis from the thread corpus, but local data is not dense enough yet "
        f"({snapshots}/{minimum_snapshots} snapshots). Treat this as collection guidance, not a PnL signal."
    )


def market_row(row: asyncpg.Record, coverage: asyncpg.Record | None) -> dict[str, Any]:
    return {
        "condition_id": row["condition_id"],
        "question": row["question"],
        "category": row["category"],
        "active": row["active"],
        "closed": row["closed"],
        "volume": row["volume"],
        "liquidity": row["liquidity"],
        "end_date": row["end_date"],
        "snapshots": coverage["snapshots"] if coverage else 0,
        "avg_spread": coverage["avg_spread"] if coverage else None,
    }


def render_report(results: list[EdgeTestResult]) -> str:
    generated_at = datetime.now(UTC).isoformat()
    sections = []
    for result in results:
        sections.append(
            f"""## {result.family}
- Status: `{result.status}`
- Candidate markets: {result.candidate_markets}
- Covered markets: {result.covered_markets}
- Snapshots: {result.snapshots}
- Hypothesis: {result.hypothesis}
- Verdict: {result.verdict}
- Next action: {result.next_action}

### Blockers
{bullets(result.blockers or ["No blocker detected."])}

### Sample Markets
{render_market_table(result.sample_markets)}
"""
        )
    return f"""{render_frontmatter({"type": "edge-research-tests", "tags": ["research", "edge", "paper-only"]})}
# Edge Research Test Results

Generated at: `{generated_at}`

Mode: `research_readiness_only`

No live trading, no order placement, no private key usage. These tests only inspect local market metadata and stored orderbook snapshots.

{chr(10).join(sections)}
"""


def render_market_table(markets: list[dict[str, Any]]) -> str:
    if not markets:
        return "No matching markets."
    lines = [
        "| Snapshots | Category | Market | Condition ID |",
        "|---:|---|---|---|",
    ]
    for row in markets:
        lines.append(
            f"| {row['snapshots']} | {row.get('category') or ''} | "
            f"{str(row.get('question') or '')[:90]} | `{row.get('condition_id')}` |"
        )
    return "\n".join(lines)


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def normalize_database_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async()))
