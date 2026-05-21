#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smart money wallet tracker — aggregate positions from top Polymarket traders.

Usage:
    PYTHONPATH=src python scripts/scan_smart_money.py
    PYTHONPATH=src python scripts/scan_smart_money.py --min-wallets 2 --obsidian
    PYTHONPATH=src python scripts/scan_smart_money.py --top 20 --json-out tmp/smart_money.json
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from polybot.core.config import get_settings
from polybot.polymarket.api import PolymarketClient

# ── Watchlist ────────────────────────────────────────────────────────────────
# Source: obsidian-vault/Research/Wallets-To-Watch/wallets-to-watch.md
# Only wallet addresses that are directly verifiable on-chain.
# Usernames (@pbot-6 etc.) need resolution via Gamma profile endpoint — added separately.
WATCHLIST: list[dict[str, str]] = [
    # Tier 1 — High conviction, architecture described
    {
        "address": "0xe1d6b51521bd4365769199f392f9818661bd907",
        "label": "HFT-crypto-728k",
        "tier": "1",
        "note": "$728K/month HFT crypto markets",
    },
    # Tier 1 — Top leaderboard traders with documented edge (@0xChaseTM thread)
    {
        "address": "0xb40e89677d59665d5188541ad860450a6e2a7cc9",
        "label": "Poligarch",
        "tier": "1",
        "note": "$132K profit, 20K trades — systematic longshot fader (SC-001 aligned)",
    },
    {
        "address": "0x44c1dfe43260c94ed4f1d00de2e1f80fb113ebc1",
        "label": "aenews2",
        "tier": "1",
        "note": "$1.94M profit, 2583 trades — overreaction fader, buys near-impossible sides",
    },
    {
        "address": "0x5bffcf561bcae83af680ad600cb99f1184d6ffbe",
        "label": "YatSen",
        "tier": "1",
        "note": "$2.3M profit, 702 trades — anchoring bias exploiter, patient multi-week setups",
    },
    {
        "address": "0xec981ed70ae69c5cbcac08c1ba063e734f6bafcd",
        "label": "0xheavy888",
        "tier": "1",
        "note": "$772K profit, 4579 trades — end-of-event bias, thin esports markets near resolution",
    },
    {
        "address": "0x9d84ce0306f8551e02efef1680475fc0f1dc1344",
        "label": "ImJustKen",
        "tier": "1",
        "note": "$3.03M profit, 9650 trades — reflexivity trader, pre-narrative entries",
    },
    # Tier 3 — BTC 5-min bots (source: @0xRicker)
    {
        "address": "0xf705fa045201391d9632b7f3cde06a5e24453ca7",
        "label": "btc-bot-A",
        "tier": "3",
        "note": "BTC 5-min bot from @0xRicker list",
    },
    {
        "address": "0x1979ae6b7e6534de9c4539d0c205e582ca637c9d",
        "label": "btc-bot-B",
        "tier": "3",
        "note": "BTC 5-min bot from @0xRicker list",
    },
]


async def fetch_wallet(client: PolymarketClient, entry: dict[str, str]) -> dict[str, Any]:
    """Fetch positions and PnL for one wallet. Returns enriched wallet dict."""
    address = entry["address"]
    result: dict[str, Any] = {**entry, "positions": [], "pnl": None, "error": None}
    try:
        positions = await client.get_wallet_positions(address, limit=500)
        result["positions"] = positions
    except Exception as exc:
        result["error"] = f"positions: {exc}"

    try:
        pnl_data = await client.get_wallet_pnl(address)
        result["pnl"] = pnl_data
    except Exception as exc:
        result["error"] = (result["error"] or "") + f" | pnl: {exc}"

    return result


def aggregate_markets(wallets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group positions by market and count smart money wallets per market."""
    market_data: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "condition_id": "",
        "question": "",
        "outcome": "",
        "wallets": [],
        "total_exposure_usd": Decimal("0"),
        "directions": [],
    })

    for wallet in wallets:
        label = wallet.get("label", wallet["address"][:10])
        tier = wallet.get("tier", "?")
        for pos in wallet.get("positions", []):
            if not isinstance(pos, dict):
                continue
            cid = str(pos.get("conditionId") or pos.get("condition_id") or pos.get("market") or "")
            if not cid:
                continue

            question = str(pos.get("title") or pos.get("question") or pos.get("market") or cid[:40])
            outcome = str(pos.get("outcome") or pos.get("side") or "")
            size = Decimal(str(pos.get("size") or pos.get("currentValue") or pos.get("value") or 0))
            avg_price = Decimal(str(pos.get("avgPrice") or pos.get("avgCost") or pos.get("price") or 0))
            exposure = size * avg_price if avg_price > 0 else size

            entry = market_data[cid]
            entry["condition_id"] = cid
            entry["question"] = question
            entry["outcome"] = outcome
            entry["total_exposure_usd"] += exposure
            entry["wallets"].append({"label": label, "tier": tier, "exposure": float(exposure), "outcome": outcome})
            entry["directions"].append(outcome)

    rows = []
    for cid, data in market_data.items():
        wallet_count = len(data["wallets"])
        direction_votes: dict[str, int] = defaultdict(int)
        for d in data["directions"]:
            direction_votes[d.upper()] += 1
        consensus = max(direction_votes, key=direction_votes.__getitem__) if direction_votes else "?"
        rows.append({
            "condition_id": cid,
            "question": data["question"][:60],
            "consensus": consensus,
            "wallet_count": wallet_count,
            "total_exposure_usd": float(data["total_exposure_usd"]),
            "wallets": data["wallets"],
        })

    return sorted(rows, key=lambda r: (r["wallet_count"], r["total_exposure_usd"]), reverse=True)


async def run() -> int:
    parser = argparse.ArgumentParser(description="Smart money wallet tracker")
    parser.add_argument("--min-wallets", type=int, default=1, help="Min number of smart wallets per market to show")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--obsidian", action="store_true")
    parser.add_argument("--json-out", type=Path, default=Path("tmp/smart_money_scan.json"))
    args = parser.parse_args()

    settings = get_settings()

    print(f"\nFetching positions for {len(WATCHLIST)} tracked wallets...")
    async with PolymarketClient(settings) as client:
        tasks = [fetch_wallet(client, w) for w in WATCHLIST]
        wallets = await asyncio.gather(*tasks)

    wallets_ok = [w for w in wallets if not w["error"]]
    wallets_err = [w for w in wallets if w["error"]]
    print(f"  -> {len(wallets_ok)} wallets OK, {len(wallets_err)} errors")
    for w in wallets_err:
        print(f"     [!] {w['label']}: {w['error']}")

    markets = aggregate_markets(list(wallets))
    markets = [m for m in markets if m["wallet_count"] >= args.min_wallets]
    top = markets[:args.top]

    print(f"\n{'='*95}")
    print(f"{'#':<3} {'Question':<55} {'Consensus':>9} {'Wallets':>7} {'Exposure$':>10}")
    print(f"{'='*95}")
    for i, m in enumerate(top, 1):
        print(
            f"{i:<3} {m['question']:<55} "
            f"{m['consensus']:>9} "
            f"{m['wallet_count']:>7} "
            f"${m['total_exposure_usd']:>9,.0f}"
        )

    if not top:
        print("No positions found. Wallets may have no open positions or API returned empty.")
    else:
        print(f"\nTop market by wallet count: [{top[0]['consensus']}] {top[0]['question']}")
        print(f"  condition_id: {top[0]['condition_id']}")
        if len(top[0]['wallets']) > 1:
            print(f"  Wallets in: " + ", ".join(w['label'] for w in top[0]['wallets']))

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(top, indent=2, default=str), encoding="utf-8")
    print(f"\nJSON → {args.json_out}")

    if args.obsidian:
        from polybot.knowledge.obsidian import ObsidianVault
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()
        scan_date = date.today().isoformat()
        lines = [
            f"---",
            f"tags: [smart-money, wallets, {scan_date}]",
            f"date: {scan_date}",
            f"wallets_tracked: {len(WATCHLIST)}",
            f"markets_found: {len(markets)}",
            f"---",
            f"",
            f"# Smart Money Scan — {scan_date}",
            f"",
            f"**Wallets suivis** : {len(WATCHLIST)} | **Marchés avec positions** : {len(markets)}",
            f"",
        ]
        if top:
            lines.append("## Marchés actifs (triés par nombre de smart wallets)")
            lines.append("")
            lines.append("| # | Question | Consensus | Wallets | Exposure$ |")
            lines.append("|---|----------|-----------|---------|-----------|")
            for i, m in enumerate(top, 1):
                lines.append(f"| {i} | {m['question'][:55]} | {m['consensus']} | {m['wallet_count']} | ${m['total_exposure_usd']:,.0f} |")
            lines.append("")
            lines.append("## Détail wallets")
            for m in top[:5]:
                lines.append(f"\n### {m['question'][:60]}")
                lines.append(f"- `{m['condition_id']}`")
                for w in m["wallets"]:
                    lines.append(f"  - [{w['tier']}] {w['label']} → {w['outcome']} (${w['exposure']:,.0f})")
        else:
            lines.append("Aucune position ouverte trouvée sur les wallets suivis.")

        lines.append(f"\n→ `{args.json_out}`")
        note_path = vault.write_note(
            "Research/Smart-Money",
            f"Smart Money Scan {scan_date}",
            "\n".join(lines),
            overwrite=True,
        )
        print(f"Obsidian → {note_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
