#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SC-003 — Dual-leg arbitrage detector (Jeremy Whittaker strategy).

Scans binary Polymarket markets for combined YES+NO ask price < $1.00 using
real CLOB orderbook data. The Gamma API prices always sum to $1.00 (mid-prices),
so we must check actual best-ask prices from the CLOB to find true arb.

When YES_ask + NO_ask < $1.00, buying both legs guarantees $1.00 at resolution
regardless of outcome — risk-free profit equal to (1.00 - combined_ask).

Usage:
    PYTHONPATH=src python scripts/scan_dual_leg_arb.py
    PYTHONPATH=src python scripts/scan_dual_leg_arb.py --min-edge 0.005 --min-volume 10000
    PYTHONPATH=src python scripts/scan_dual_leg_arb.py --category crypto --obsidian
    PYTHONPATH=src python scripts/scan_dual_leg_arb.py --top-markets 50 --min-edge 0.002
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from polybot.core.config import get_settings
from polybot.polymarket.api import PolymarketClient


def _best_ask(book: dict) -> float | None:
    """Return best ask price from a CLOB orderbook dict."""
    asks = book.get("asks") or []
    if not asks:
        return None
    try:
        return min(float(a["price"]) for a in asks if a.get("price"))
    except Exception:
        return None


def _best_bid(book: dict) -> float | None:
    """Return best bid price from a CLOB orderbook dict."""
    bids = book.get("bids") or []
    if not bids:
        return None
    try:
        return max(float(b["price"]) for b in bids if b.get("price"))
    except Exception:
        return None


async def check_market_arb(
    client: PolymarketClient,
    market: dict,
    min_edge: float,
) -> dict | None:
    """Fetch CLOB orderbooks for a market and check dual-leg edge."""
    token_ids = market.get("token_ids", [])
    if len(token_ids) < 2:
        return None

    yes_token, no_token = token_ids[0], token_ids[1]
    outcomes = market.get("outcomes", [])
    yes_label = str(outcomes[0]) if outcomes else "YES"
    no_label = str(outcomes[1]) if len(outcomes) > 1 else "NO"

    try:
        books = await client.get_orderbooks([yes_token, no_token])
    except Exception:
        return None

    if len(books) < 2:
        return None

    yes_ask = _best_ask(books[0])
    no_ask = _best_ask(books[1])
    yes_bid = _best_bid(books[0])
    no_bid = _best_bid(books[1])

    if yes_ask is None or no_ask is None:
        return None

    combined_ask = yes_ask + no_ask
    edge = 1.0 - combined_ask

    if edge < min_edge:
        return None

    return {
        "condition_id": market["condition_id"],
        "question": market["question"][:80],
        "category": market["category"],
        "yes_ask": round(yes_ask, 4),
        "no_ask": round(no_ask, 4),
        "yes_bid": round(yes_bid, 4) if yes_bid else None,
        "no_bid": round(no_bid, 4) if no_bid else None,
        "combined_ask": round(combined_ask, 4),
        "edge": round(edge, 4),
        "edge_pct": round(edge * 100, 2),
        "volume_usd": market["volume"],
        "yes_token": yes_token,
        "no_token": no_token,
        "yes_label": yes_label,
        "no_label": no_label,
        "end_date": market.get("end_date", ""),
    }


async def run() -> int:
    parser = argparse.ArgumentParser(description="SC-003 Dual-leg arbitrage scanner")
    parser.add_argument("--min-edge", type=float, default=0.003, help="Min combined edge (default 0.3%%)")
    parser.add_argument("--min-volume", type=float, default=10_000, help="Min market volume USD")
    parser.add_argument("--category", type=str, default="", help="Filter by category (e.g. crypto)")
    parser.add_argument("--top-markets", type=int, default=100, help="Top N markets by volume to check CLOB")
    parser.add_argument("--top", type=int, default=20, help="Display top N results")
    parser.add_argument("--obsidian", action="store_true")
    parser.add_argument("--json-out", type=Path, default=Path("tmp/dual_leg_arb.json"))
    args = parser.parse_args()

    settings = get_settings()
    today = date.today().isoformat()

    print(f"\n{'='*70}")
    print(f"SC-003 DUAL-LEG ARB SCANNER — {today}")
    print(f"Min edge: {args.min_edge:.2%} | Min volume: ${args.min_volume:,.0f}")
    print(f"Checking top {args.top_markets} markets by volume via CLOB orderbooks")
    print(f"{'='*70}")

    # Fetch market list
    all_markets: list[dict] = []
    async with PolymarketClient(settings) as client:
        print("\nFetching market list...")
        for page in range(10):
            batch = await client.list_markets(active=True, closed=False, limit=500, offset=page * 500)
            if not batch:
                break
            all_markets.extend(batch)

        print(f"  {len(all_markets)} active markets loaded")

        # Parse binary markets with enough volume
        candidates: list[dict] = []
        for m in all_markets:
            try:
                prices = json.loads(m.get("outcomePrices") or "[]")
                outcomes = json.loads(m.get("outcomes") or "[]")
                token_ids = json.loads(m.get("clobTokenIds") or "[]")
            except Exception:
                continue

            if len(outcomes) != 2 or len(token_ids) < 2:
                continue

            vol = float(m.get("volumeNum") or m.get("volume") or 0)
            if vol < args.min_volume:
                continue

            if args.category:
                cat = str(m.get("category") or "").lower()
                if args.category.lower() not in cat:
                    continue

            candidates.append({
                "condition_id": str(m.get("conditionId") or ""),
                "question": str(m.get("question") or "")[:80],
                "category": str(m.get("category") or ""),
                "volume": vol,
                "token_ids": token_ids[:2],
                "outcomes": outcomes[:2],
                "end_date": str(m.get("endDate") or ""),
            })

        # Sort by volume desc, take top N for CLOB checking
        candidates.sort(key=lambda x: x["volume"], reverse=True)
        to_check = candidates[:args.top_markets]

        print(f"  {len(candidates)} binary markets ≥ ${args.min_volume:,.0f}")
        print(f"  Checking CLOB orderbooks for top {len(to_check)} by volume...")

        # Check orderbooks
        opps: list[dict] = []
        for i, market in enumerate(to_check):
            result = await check_market_arb(client, market, min_edge=args.min_edge)
            if result:
                opps.append(result)
            if (i + 1) % 10 == 0:
                print(f"  Checked {i+1}/{len(to_check)}... ({len(opps)} opps found)", end="\r")

    print(f"\n  Done — {len(to_check)} markets checked, {len(opps)} opportunities found")

    opps.sort(key=lambda x: x["edge"], reverse=True)

    # Display results
    print(f"\n{'='*105}")
    print(f"{'#':<4} {'Question':<52} {'Cat':<8} {'Y-Ask':>5} {'N-Ask':>5} {'Comb':>6} {'Edge%':>6} {'Vol$M':>7}")
    print(f"{'='*105}")

    for i, opp in enumerate(opps[:args.top], 1):
        print(
            f"{i:<4} {opp['question'][:52]:<52} "
            f"{opp['category'][:8]:<8} "
            f"{opp['yes_ask']:>5.3f} "
            f"{opp['no_ask']:>5.3f} "
            f"{opp['combined_ask']:>6.4f} "
            f"{opp['edge_pct']:>+5.2f}%"
            f"{opp['volume_usd']/1e6:>7.2f}M"
        )

    if not opps:
        print("No dual-leg arb opportunities found at current thresholds.")
        print(f"  Try: --min-edge 0.001 --top-markets 200")
        print(f"  Note: Polymarket is generally efficient; combined_ask ≈ $1.00 most of the time.")
    else:
        best = opps[0]
        print(f"\n⭐ BEST: {best['question'][:65]}")
        print(f"   YES ask {best['yes_ask']:.4f} + NO ask {best['no_ask']:.4f} = {best['combined_ask']:.4f} → edge {best['edge_pct']:+.2f}%")
        print(f"   Vol: ${best['volume_usd']:,.0f} | condition_id: {best['condition_id']}")
        print(f"\n   ⚠️  Execution risk: both legs must fill simultaneously.")
        print(f"      One-legged fill = unintended directional position.")

    # Always show stats
    print(f"\nStats: {len(candidates)} binary markets found | {len(to_check)} CLOB-checked | {len(opps)} with edge ≥ {args.min_edge:.2%}")

    # Save JSON
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(opps, indent=2, default=str), encoding="utf-8")
    print(f"JSON → {args.json_out}")

    if args.obsidian:
        from polybot.knowledge.obsidian import ObsidianVault
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()

        lines = [
            f"---",
            f"tags: [sc-003, dual-leg-arb, arbitrage, {today}]",
            f"date: {today}",
            f"opportunities: {len(opps)}",
            f"markets_checked: {len(to_check)}",
            f"best_edge: {opps[0]['edge_pct']:.2f}" if opps else "best_edge: 0",
            f"---",
            f"",
            f"# SC-003 Dual-Leg Arbitrage — {today}",
            f"",
            f"**Marchés scannés** : {len(candidates)} binaires ≥ ${args.min_volume:,.0f} | "
            f"**CLOB vérifiés** : {len(to_check)} | **Opportunités** : {len(opps)}",
            f"**Seuil** : edge > {args.min_edge:.2%}",
            f"",
        ]

        if opps:
            lines += [
                f"## Opportunités (YES ask + NO ask < $1.00)",
                f"",
                f"| # | Question | Y-Ask | N-Ask | Combiné | Edge% | Volume |",
                f"|---|----------|-------|-------|---------|-------|--------|",
            ]
            for i, opp in enumerate(opps[:args.top], 1):
                lines.append(
                    f"| {i} | {opp['question'][:55]} | {opp['yes_ask']:.3f} | {opp['no_ask']:.3f} | "
                    f"{opp['combined_ask']:.4f} | {opp['edge_pct']:+.2f}% | ${opp['volume_usd']:,.0f} |"
                )
            best = opps[0]
            lines += [
                f"",
                f"## Meilleure opportunité",
                f"",
                f"**{best['question']}**",
                f"- YES ask : {best['yes_ask']:.4f} | NO ask : {best['no_ask']:.4f}",
                f"- Combiné : {best['combined_ask']:.4f} → Edge **{best['edge_pct']:+.2f}%**",
                f"- Volume : ${best['volume_usd']:,.0f}",
                f"- `{best['condition_id']}`",
            ]
        else:
            lines.append(
                f"Aucune opportunité trouvée (seuil {args.min_edge:.2%}). "
                f"Polymarket est généralement efficient — combined_ask ≈ $1.00."
            )

        lines += [
            f"",
            f"## Notes d'exécution",
            f"",
            f"- Edge \"garanti\" théoriquement : acheter YES + NO = $1.00 reçu à résolution quelle que soit l'issue",
            f"- **Risque critique** : si une seule jambe remplit → position directionnelle non voulue",
            f"- Stratégie à valider d'abord en paper trading avec exécution atomique des deux jambes",
            f"- Frais makers = 0% sur Polymarket — l'edge calculé est net de frais si post-only",
            f"",
            f"→ `{args.json_out}`",
        ]

        note_path = vault.write_note(
            "Research/Arbitrage",
            f"SC-003 Dual-Leg Arb {today}",
            "\n".join(lines),
            overwrite=True,
        )
        print(f"Obsidian → {note_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
