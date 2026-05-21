#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SC-011 — Behavioral Bias Scanner (Overreaction + Anchoring).

Detects two structural mispricings from @0xChaseTM's "Iceberg" thread:

OVERREACTION BIAS (aenews2 style, $1.94M profit):
  News drops → price jumps 20¢ in 30s → retail piles in →
  liquidity catches up → price reverts to base rate.
  Signal: large price move (>15%) detected, wait for fade.

ANCHORING BIAS (YatSen style, $2.3M, 702 trades):
  Market stable for 2+ weeks → fundamental shift → price barely moves →
  still anchored to old level despite new information.
  Signal: price in tight range for 7+ days, fundamentals should have moved it.

Uses Polymarket price history API (/prices-history) to detect both patterns.

Usage:
    PYTHONPATH=src python scripts/scan_behavioral_bias.py
    PYTHONPATH=src python scripts/scan_behavioral_bias.py --mode overreaction
    PYTHONPATH=src python scripts/scan_behavioral_bias.py --mode anchoring --obsidian
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, stdev

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from polybot.core.config import get_settings
from polybot.polymarket.api import PolymarketClient


def _price_stats(history: list[dict]) -> dict:
    """Compute price stats from price history data (fidelity=60 → 1-hour points)."""
    pairs = sorted(
        ((int(p["t"]), float(p["p"])) for p in history if "p" in p and "t" in p),
        key=lambda x: x[0],
    )
    if not pairs:
        return {}

    timestamps, prices = zip(*pairs)
    prices = list(prices)
    current = prices[-1]

    # With fidelity=60 data, each point is ~1 hour → 168 points = 7 days, 720 = 30 days
    recent_7d = prices[-168:] if len(prices) >= 168 else prices
    last_30d = prices

    price_std = stdev(last_30d) if len(last_30d) > 1 else 0
    price_range_7d = max(recent_7d) - min(recent_7d)
    price_mean_7d = mean(recent_7d)

    # Recent move = last 24h (last 24 hourly points) vs now
    day_ago_price = prices[-24] if len(prices) >= 24 else prices[0]
    recent_move = current - day_ago_price

    return {
        "current": current,
        "mean_7d": round(price_mean_7d, 4),
        "std_30d": round(price_std, 4),
        "range_7d": round(price_range_7d, 4),
        "recent_move": round(recent_move, 4),
        "n_points": len(prices),
    }


def detect_overreaction(stats: dict, *, min_move: float = 0.12) -> dict | None:
    """Detect price overreaction: large recent move likely to revert."""
    move = abs(stats.get("recent_move", 0))
    if move < min_move:
        return None
    current = stats.get("current", 0.5)
    # Direction of fade trade
    if stats["recent_move"] > 0:
        # Price jumped UP → fade by buying NO (or selling YES)
        fade_side = "NO"
        fade_price = 1.0 - current
    else:
        # Price dropped → fade by buying YES
        fade_side = "YES"
        fade_price = current

    return {
        "bias": "overreaction",
        "signal_side": fade_side,
        "signal_price": round(fade_price, 4),
        "recent_move_pct": round(stats["recent_move"] * 100, 2),
        "current_price": round(current, 4),
        "mean_7d": stats.get("mean_7d", 0),
        "description": f"Price moved {stats['recent_move']:+.2%} recently. Fade: buy {fade_side} at {fade_price:.3f}.",
    }


def detect_anchoring(stats: dict, *, max_range_7d: float = 0.08, min_std: float = 0.02) -> dict | None:
    """Detect anchoring: tight price range for 7d despite meaningful volatility in broader window."""
    range_7d = stats.get("range_7d", 1.0)
    std_30d = stats.get("std_30d", 0)
    current = stats.get("current", 0.5)

    # Market is anchored if: recent range is tight AND historical vol is higher
    # This suggests price is stuck despite the market having moved before
    if range_7d > max_range_7d:
        return None
    if std_30d < min_std:
        return None  # Market has always been tight — no anchoring

    # Anchoring is more interesting when current price is at an extreme the crowd anchored to
    # The play: if fundamentals have shifted, the anchor will eventually break
    return {
        "bias": "anchoring",
        "signal_side": "MONITOR",  # No clear direction without external fundamental data
        "signal_price": round(current, 4),
        "range_7d": round(range_7d, 4),
        "std_30d": round(std_30d, 4),
        "current_price": round(current, 4),
        "mean_7d": stats.get("mean_7d", 0),
        "description": f"7d range only {range_7d:.2%} but historical std {std_30d:.2%}. Market anchored at {current:.3f}.",
    }


async def run() -> int:
    parser = argparse.ArgumentParser(description="SC-011 Behavioral bias scanner")
    parser.add_argument("--mode", choices=["overreaction", "anchoring", "both"], default="both")
    parser.add_argument("--min-volume", type=float, default=50_000)
    parser.add_argument("--min-move", type=float, default=0.12, help="Min recent price move for overreaction (default 12%%)")
    parser.add_argument("--top-markets", type=int, default=50, help="Top N markets by volume to scan")
    parser.add_argument("--top", type=int, default=20, help="Display top N results")
    parser.add_argument("--obsidian", action="store_true")
    parser.add_argument("--json-out", type=Path, default=Path("tmp/behavioral_bias_signals.json"))
    args = parser.parse_args()

    settings = get_settings()
    today = date.today().isoformat()

    print(f"\n{'='*70}")
    print(f"SC-011 BEHAVIORAL BIAS SCANNER — {today}")
    print(f"Mode: {args.mode} | Min vol: ${args.min_volume:,.0f} | Top {args.top_markets} markets")
    print(f"{'='*70}")

    all_markets: list[dict] = []
    async with PolymarketClient(settings) as client:
        print("\nFetching high-volume markets...")
        for page in range(10):
            batch = await client.list_markets(active=True, closed=False, limit=500, offset=page * 500)
            if not batch:
                break
            all_markets.extend(batch)

    # Filter to binary markets with enough volume
    candidates = []
    for m in all_markets:
        vol = float(m.get("volumeNum") or 0)
        if vol < args.min_volume:
            continue
        try:
            outcomes = json.loads(m.get("outcomes") or "[]")
            token_ids = json.loads(m.get("clobTokenIds") or "[]")
            prices = json.loads(m.get("outcomePrices") or "[]")
        except Exception:
            continue
        if len(outcomes) != 2 or not token_ids:
            continue
        p0 = float(prices[0]) if prices else 0.5
        if p0 < 0.02 or p0 > 0.98:
            continue  # Near-resolved
        candidates.append({
            "condition_id": str(m.get("conditionId") or ""),
            "question": str(m.get("question") or "")[:80],
            "category": str(m.get("category") or ""),
            "volume": vol,
            "token_id": str(token_ids[0]),
            "current_price": p0,
        })

    candidates.sort(key=lambda x: x["volume"], reverse=True)
    to_scan = candidates[:args.top_markets]
    print(f"  {len(candidates)} binary markets ≥ ${args.min_volume:,.0f} | scanning top {len(to_scan)}")

    signals: list[dict] = []

    from datetime import datetime as _dt, timezone as _tz
    start_30d = int((_dt.now(_tz.utc).timestamp()) - 30 * 86400)

    async with PolymarketClient(settings) as client:
        for i, market in enumerate(to_scan):
            try:
                # Fetch 30-day hourly price history via startTs + fidelity=60 (1h resolution)
                history_data = await client.get_price_history(
                    token_id=market["token_id"],
                    start_ts=start_30d,
                    fidelity=60,
                )
                history = history_data.get("history", [])
            except Exception:
                continue

            if len(history) < 10:
                continue

            stats = _price_stats(history)
            if not stats:
                continue

            if args.mode in ("overreaction", "both"):
                sig = detect_overreaction(stats, min_move=args.min_move)
                if sig:
                    signals.append({**market, **sig, "price_stats": stats})

            if args.mode in ("anchoring", "both"):
                sig = detect_anchoring(stats)
                if sig:
                    signals.append({**market, **sig, "price_stats": stats})

            if (i + 1) % 10 == 0:
                print(f"  Scanned {i+1}/{len(to_scan)}... ({len(signals)} signals)", end="\r")

    print(f"\n  Done — {len(to_scan)} markets checked, {len(signals)} bias signals found")

    # Sort by magnitude of move/anchoring
    signals.sort(key=lambda x: abs(x.get("recent_move_pct", 0) or x.get("range_7d", 0)), reverse=True)

    overreaction = [s for s in signals if s.get("bias") == "overreaction"]
    anchoring = [s for s in signals if s.get("bias") == "anchoring"]

    print(f"\n{'='*110}")
    print(f"{'#':<3} {'Question':<52} {'Bias':<14} {'Side':>4} {'Price':>6} {'Move%/Rng':>10} {'Vol$M':>7}")
    print(f"{'='*110}")

    for i, sig in enumerate(signals[:args.top], 1):
        bias_label = "OVERREACT" if sig["bias"] == "overreaction" else "ANCHOR"
        move_val = f"{sig.get('recent_move_pct', 0):+.1f}%" if sig["bias"] == "overreaction" else f"{sig.get('range_7d', 0):.2%}"
        print(
            f"{i:<3} {sig['question'][:52]:<52} "
            f"{bias_label:<14} "
            f"{sig.get('signal_side', ''):>4} "
            f"{sig.get('signal_price', 0):>6.3f} "
            f"{move_val:>10} "
            f"{sig['volume']/1e6:>7.2f}M"
        )

    if overreaction:
        best = overreaction[0]
        print(f"\n⭐ TOP OVERREACTION: [{best['signal_side']}] {best['question'][:65]}")
        print(f"   {best['description']}")
        print(f"   Vol: ${best['volume']:,.0f} | Category: {best['category']}")
    if anchoring:
        best = anchoring[0]
        print(f"\n⚓ TOP ANCHOR: {best['question'][:65]}")
        print(f"   {best['description']}")

    if not signals:
        print("No behavioral bias signals found at current thresholds.")
        print(f"  Try: --min-move 0.08 --min-volume 20000")

    print(f"\nStats: {len(overreaction)} overreaction | {len(anchoring)} anchoring")

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    # Remove price_stats from JSON to keep it compact
    clean = [{k: v for k, v in s.items() if k != "price_stats"} for s in signals]
    args.json_out.write_text(json.dumps(clean, indent=2, default=str), encoding="utf-8")
    print(f"JSON → {args.json_out}")

    if args.obsidian and signals:
        from polybot.knowledge.obsidian import ObsidianVault
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()

        lines = [
            f"---",
            f"tags: [sc-011, behavioral-bias, overreaction, anchoring, {today}]",
            f"date: {today}",
            f"overreaction_signals: {len(overreaction)}",
            f"anchoring_signals: {len(anchoring)}",
            f"---",
            f"",
            f"# SC-011 Behavioral Bias — {today}",
            f"",
            f"**Source** : @0xChaseTM 'Iceberg' thread | Top {args.top_markets} marchés scannés",
            f"**Overreaction** : {len(overreaction)} signaux | **Anchoring** : {len(anchoring)} signaux",
            f"",
            f"## Overreaction (style aenews2 — $1.94M)",
            f"Prix saute >12% → retail entre → liquidité rattrapée → réversion vers base rate.",
            f"",
        ]
        if overreaction:
            lines += ["| # | Question | Side | Prix | Move% | Vol |", "|---|----------|------|------|-------|-----|"]
            for i, s in enumerate(overreaction[:10], 1):
                lines.append(f"| {i} | {s['question'][:50]} | {s['signal_side']} | {s['signal_price']:.3f} | {s.get('recent_move_pct', 0):+.1f}% | ${s['volume']:,.0f} |")
        else:
            lines.append("Aucun signal overreaction.")

        lines += [
            f"",
            f"## Anchoring (style YatSen — $2.3M)",
            f"Range 7j < 8% mais std historique > 2% → prix ancré malgré conditions changeantes.",
            f"",
        ]
        if anchoring:
            lines += ["| # | Question | Prix | Range7j | Std30j | Vol |", "|---|----------|------|---------|--------|-----|"]
            for i, s in enumerate(anchoring[:10], 1):
                lines.append(f"| {i} | {s['question'][:50]} | {s['signal_price']:.3f} | {s.get('range_7d', 0):.2%} | {s.get('std_30d', 0):.2%} | ${s['volume']:,.0f} |")
        else:
            lines.append("Aucun signal anchoring.")

        lines += [
            f"",
            f"## Wallets de référence",
            f"- **aenews2** `0x44c1dfe43260c94ed4f1d00de2e1f80fb113ebc1` — $1.94M, overreaction fader",
            f"- **YatSen** `0x5bffcf561bcae83af680ad600cb99f1184d6ffbe` — $2.3M, anchoring exploiter",
            f"",
            f"→ `{args.json_out}`",
        ]

        note_path = vault.write_note(
            "Research/Edge-Research",
            f"SC-011 Behavioral Bias {today}",
            "\n".join(lines),
            overwrite=True,
        )
        print(f"Obsidian → {note_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
