#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SC-009 — End-of-Event Bias Scanner.

Scans binary markets expiring within 72h for the structural mispricing
described in @0xChaseTM's "Iceberg" thread:

  M(t) = α × σ × √(T-t) × (1/L(t))

As T approaches, LPs withdraw faster than volatility decays → spread widens
→ favourites trade at discount, longshots at premium.

Filter: T-t < 72h AND daily_volume < $50K AND price away from fair value.
Signal: bid/ask mid-price vs 5-day MA or Becker-corrected probability.

Usage:
    PYTHONPATH=src python scripts/scan_end_of_event.py
    PYTHONPATH=src python scripts/scan_end_of_event.py --max-hours 48 --min-edge 0.05
    PYTHONPATH=src python scripts/scan_end_of_event.py --claude --obsidian
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from polybot.core.config import get_settings
from polybot.polymarket.api import PolymarketClient
from polybot.research.signals.becker_oracle import becker_correction


def hours_to_resolution(end_date_str: str) -> float | None:
    """Parse endDate and return hours until resolution. None if unparseable."""
    if not end_date_str:
        return None
    now = datetime.now(timezone.utc)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(end_date_str, fmt).replace(tzinfo=timezone.utc)
            return (dt - now).total_seconds() / 3600
        except ValueError:
            continue
    # Fallback: truncate to 19 chars
    try:
        dt = datetime.strptime(end_date_str[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        return (dt - now).total_seconds() / 3600
    except Exception:
        return None


def becker_edge(price: float) -> float:
    """Edge if betting NO on this price (longshot correction)."""
    corrected = becker_correction(price)
    return (1.0 - corrected) - (1.0 - price)  # NO edge


def classify_market(price: float, hours_left: float, volume: float) -> dict:
    """Classify a market for end-of-event dislocation."""
    # Category per @0xChaseTM playbook
    is_favourite = price >= 0.65
    is_longshot = price <= 0.30
    is_near_resolution = hours_left < 72

    # Favourite panic discount: late + high price + thin liquidity
    fav_discount = is_favourite and is_near_resolution and volume < 50_000
    # Longshot hope premium: late + low price (people holding hope)
    long_premium = is_longshot and is_near_resolution and volume < 50_000

    edge_type = None
    if fav_discount:
        edge_type = "favourite_discount"  # Buy YES — market unfairly discounted
    elif long_premium:
        edge_type = "longshot_premium"  # Buy NO — longshot unfairly expensive

    return {
        "is_favourite": is_favourite,
        "is_longshot": is_longshot,
        "is_near_resolution": is_near_resolution,
        "fav_discount": fav_discount,
        "long_premium": long_premium,
        "edge_type": edge_type,
    }


async def run() -> int:
    parser = argparse.ArgumentParser(description="SC-009 End-of-event bias scanner")
    parser.add_argument("--max-hours", type=float, default=168.0, help="Max hours to resolution (default 7d)")
    parser.add_argument("--min-hours", type=float, default=1.0, help="Min hours to resolution (avoid resolved)")
    parser.add_argument("--max-volume", type=float, default=100_000, help="Max daily volume (thin liquidity filter)")
    parser.add_argument("--min-volume", type=float, default=1_000, help="Min volume (ignore truly dead markets)")
    parser.add_argument("--min-price", type=float, default=0.55, help="Min YES price for favourite discount signal")
    parser.add_argument("--max-longshot", type=float, default=0.35, help="Max YES price for longshot premium signal")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--claude", action="store_true", help="Enrich top signals with Claude oracle")
    parser.add_argument("--obsidian", action="store_true")
    parser.add_argument("--json-out", type=Path, default=Path("tmp/end_of_event_signals.json"))
    args = parser.parse_args()

    settings = get_settings()
    today = date.today().isoformat()

    print(f"\n{'='*70}")
    print(f"SC-009 END-OF-EVENT BIAS SCANNER — {today}")
    print(f"Window: {args.min_hours:.0f}h–{args.max_hours:.0f}h | Vol < ${args.max_volume:,.0f}")
    print(f"{'='*70}")

    all_markets: list[dict] = []
    async with PolymarketClient(settings) as client:
        print("\nFetching active markets...")
        for page in range(10):
            batch = await client.list_markets(active=True, closed=False, limit=500, offset=page * 500)
            if not batch:
                break
            all_markets.extend(batch)

    print(f"  {len(all_markets)} active markets")

    signals: list[dict] = []
    now = datetime.now(timezone.utc)

    for m in all_markets:
        try:
            prices_raw = json.loads(m.get("outcomePrices") or "[]")
            outcomes_raw = json.loads(m.get("outcomes") or "[]")
        except Exception:
            continue

        if len(outcomes_raw) != 2 or len(prices_raw) != 2:
            continue

        end_date = str(m.get("endDate") or m.get("end_date_iso") or "")
        hours_left = hours_to_resolution(end_date)
        if hours_left is None or hours_left < args.min_hours or hours_left > args.max_hours:
            continue

        try:
            yes_price = float(prices_raw[0])
            no_price = float(prices_raw[1])
        except (ValueError, TypeError):
            continue

        # Skip near-fully-resolved markets (price already at extreme)
        if yes_price < 0.005 or yes_price > 0.995:
            continue

        vol = float(m.get("volumeNum") or m.get("volume") or 0)
        if vol < args.min_volume or vol > args.max_volume:
            continue

        category = str(m.get("category") or "")
        question = str(m.get("question") or "")[:80]
        condition_id = str(m.get("conditionId") or "")

        classification = classify_market(yes_price, hours_left, vol)
        if not classification["edge_type"]:
            continue

        edge_type = classification["edge_type"]

        # Becker correction for longshot premium case (YES price ≤ 0.35 → NO is a smart bet)
        becker_no_edge = becker_edge(yes_price) if yes_price <= 0.40 else 0.0

        # For favourite discount: simple heuristic — if price > 0.70 and thin book, edge is ~3-5%
        if edge_type == "favourite_discount":
            est_edge = max(0.03, 1.0 - yes_price - 0.02)  # approx LP withdrawal discount
            signal_side = "YES"
            signal_price = yes_price
        else:
            est_edge = becker_no_edge if becker_no_edge > 0.01 else 0.02
            signal_side = "NO"
            signal_price = no_price

        signals.append({
            "condition_id": condition_id,
            "question": question,
            "category": category,
            "yes_price": round(yes_price, 4),
            "no_price": round(no_price, 4),
            "hours_left": round(hours_left, 1),
            "volume_usd": vol,
            "edge_type": edge_type,
            "signal_side": signal_side,
            "signal_price": round(signal_price, 4),
            "est_edge": round(est_edge, 4),
            "becker_no_edge": round(becker_no_edge, 4),
            "end_date": end_date,
        })

    # Sort: best edge first, then soonest resolution
    signals.sort(key=lambda x: (-x["est_edge"], x["hours_left"]))

    # Claude enrichment
    if args.claude and signals and settings.anthropic_api_key:
        print(f"\n  Enriching top {min(10, len(signals))} with Claude oracle...")
        from polybot.research.signals.becker_oracle import enrich_with_claude

        oracle_rows = []
        for s in signals[:10]:
            oracle_rows.append({
                "condition_id": s["condition_id"],
                "question": s["question"],
                "volume": s["volume_usd"],
                "category": s["category"],
                "outcome": s["signal_side"],
                "price": s["signal_price"],
                "asset_id": "",
            })

        from polybot.research.signals.becker_oracle import scan_becker
        becker_sigs = scan_becker(oracle_rows, min_volume=0, price_low=0.01, price_high=0.99)
        enriched = enrich_with_claude(becker_sigs, api_key=settings.anthropic_api_key)

        # Merge Claude results back
        claude_map = {s.condition_id: s for s in enriched}
        for sig in signals[:10]:
            cs = claude_map.get(sig["condition_id"])
            if cs:
                sig["claude_edge"] = cs.claude_edge
                sig["claude_confidence"] = cs.claude_confidence
                sig["claude_key_factors"] = cs.claude_key_factors

    # Display
    fav_count = sum(1 for s in signals if s["edge_type"] == "favourite_discount")
    long_count = sum(1 for s in signals if s["edge_type"] == "longshot_premium")

    print(f"\n  Found {len(signals)} end-of-event signals ({fav_count} favourite discounts, {long_count} longshot premiums)")

    print(f"\n{'='*105}")
    print(f"{'#':<3} {'Question':<50} {'Side':>4} {'Price':>6} {'Edge%':>6} {'Hours':>6} {'Vol$K':>6} {'Type':<22}")
    print(f"{'='*105}")

    for i, sig in enumerate(signals[:args.top], 1):
        type_label = "FAV-DISC" if sig["edge_type"] == "favourite_discount" else "LONG-PREM"
        print(
            f"{i:<3} {sig['question'][:50]:<50} "
            f"{sig['signal_side']:>4} "
            f"{sig['signal_price']:>6.3f} "
            f"{sig['est_edge']:>+5.2%} "
            f"{sig['hours_left']:>6.1f}h "
            f"{sig['volume_usd']/1000:>5.0f}K "
            f"{type_label:<22}"
        )

    if signals:
        best = signals[0]
        print(f"\n⭐ TOP: [{best['signal_side']}] {best['question'][:65]}")
        print(f"   Price: {best['signal_price']:.3f} | Est edge: {best['est_edge']:+.2%} | {best['hours_left']:.1f}h left | Vol: ${best['volume_usd']:,.0f}")
        print(f"   Type: {best['edge_type']} | Category: {best['category']}")
        if best.get("claude_edge"):
            print(f"   Claude edge: {best['claude_edge']:+.2%} | Confidence: {best.get('claude_confidence', '?')}")

    if not signals:
        print(f"No end-of-event signals found. Try widening --max-hours or --max-volume.")

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(signals, indent=2, default=str), encoding="utf-8")
    print(f"\nJSON → {args.json_out}")

    if args.obsidian and signals:
        from polybot.knowledge.obsidian import ObsidianVault
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()

        lines = [
            f"---",
            f"tags: [sc-009, end-of-event, bias, {today}]",
            f"date: {today}",
            f"signals: {len(signals)}",
            f"favourite_discounts: {fav_count}",
            f"longshot_premiums: {long_count}",
            f"---",
            f"",
            f"# SC-009 End-of-Event Bias — {today}",
            f"",
            f"**Fenêtre** : {args.min_hours:.0f}h–{args.max_hours:.0f}h | "
            f"**Vol max** : ${args.max_volume:,.0f} | **Signaux** : {len(signals)}",
            f"({fav_count} favourite discounts · {long_count} longshot premiums)",
            f"",
            f"## Théorie (0xChaseTM)",
            f"",
            f"M(t) = α × σ × √(T-t) × (1/L(t))",
            f"",
            f"Quand t → T : liquidité L(t) s'effondre plus vite que σ décroît → spread s'élargit.",
            f"- **Favourite discount** : détenteurs paniqués vendent favoris à prix réduit (< probabilité juste)",
            f"- **Longshot premium** : psychology de loterie amplifie prix des longshots près de l'expiry",
            f"",
            f"## Signaux",
            f"",
            f"| # | Question | Side | Prix | Edge% | Heures | Vol$ | Type |",
            f"|---|----------|------|------|-------|--------|------|------|",
        ]
        for i, sig in enumerate(signals[:args.top], 1):
            type_label = "FAV-DISC" if sig["edge_type"] == "favourite_discount" else "LONG-PREM"
            lines.append(
                f"| {i} | {sig['question'][:50]} | {sig['signal_side']} | "
                f"{sig['signal_price']:.3f} | {sig['est_edge']:+.2%} | "
                f"{sig['hours_left']:.1f}h | ${sig['volume_usd']:,.0f} | {type_label} |"
            )

        if signals:
            best = signals[0]
            lines += [
                f"",
                f"## Meilleur signal",
                f"",
                f"**[{best['signal_side']}] {best['question']}**",
                f"- Prix : {best['signal_price']:.4f} | Edge estimé : {best['est_edge']:+.2%}",
                f"- Temps restant : {best['hours_left']:.1f}h | Vol : ${best['volume_usd']:,.0f}",
                f"- Type : {best['edge_type']} | `{best['condition_id']}`",
            ]
            if best.get("claude_edge"):
                lines.append(f"- Claude edge : {best['claude_edge']:+.2%} | Confidence : {best.get('claude_confidence')}")

        lines += [
            f"",
            f"## Wallets de référence (@0xChaseTM)",
            f"",
            f"- **0xheavy888** `0xec981ed70ae69c5cbcac08c1ba063e734f6bafcd` — $772K, 4579 trades, end-of-event spécialiste",
            f"- **Poligarch** `0xb40e89677d59665d5188541ad860450a6e2a7cc9` — $132K, 20K trades, longshot fader",
            f"",
            f"→ `{args.json_out}`",
        ]

        note_path = vault.write_note(
            "Research/Edge-Research",
            f"SC-009 End-of-Event {today}",
            "\n".join(lines),
            overwrite=True,
        )
        print(f"Obsidian → {note_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
