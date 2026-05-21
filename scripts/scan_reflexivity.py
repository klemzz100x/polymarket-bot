#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SC-012 — Reflexivity Scanner (Whale + Social Amplification Loop).

Detects the reflexivity pattern from @0xChaseTM's "Iceberg" thread:
  1. Whale enters large position (detectable via CLOB volume spike + smart money wallets)
  2. X/Twitter amplifies the move (social signal — not detected here, flag is manual)
  3. No real new fundamental information
  4. Crowd follows → price moves further → self-fulfilling loop
  5. Edge: enter early, exit when loop breaks (volume collapses)

Detection proxies (without Twitter API):
  - Large imbalance in CLOB orderbook (one side dominates)
  - Smart money wallet recently active in this market (from scan_smart_money output)
  - Price moved >5% in last 24h (reflexivity in motion)
  - Volume spike: 24h volume > 3× 7-day average

The play: if whale entered and price is moving, JOIN the loop early (not fade).
Exit signal: volume/day drops back below baseline → loop breaking.

Usage:
    PYTHONPATH=src python scripts/scan_reflexivity.py
    PYTHONPATH=src python scripts/scan_reflexivity.py --min-volume 30000 --top 20
    PYTHONPATH=src python scripts/scan_reflexivity.py --from-smart-money tmp/smart_money_scan.json --obsidian
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
from polybot.research.sizing import size_from_score


def _compute_book_imbalance(bids: list, asks: list) -> float:
    """Imbalance = (bid_size - ask_size) / (bid_size + ask_size). Range [-1, +1]."""
    bid_vol = sum(float(b.get("size", 0)) for b in bids[:5])
    ask_vol = sum(float(a.get("size", 0)) for a in asks[:5])
    total = bid_vol + ask_vol
    if total < 1e-9:
        return 0.0
    return (bid_vol - ask_vol) / total


def _price_velocity(history: list[dict]) -> dict:
    """Compute price move in last 24h and volume spike ratio from hourly history."""
    pairs = sorted(
        ((int(p["t"]), float(p["p"])) for p in history if "p" in p and "t" in p),
        key=lambda x: x[0],
    )
    if len(pairs) < 48:
        return {}

    timestamps, prices = zip(*pairs)
    prices = list(prices)

    current = prices[-1]
    price_24h_ago = prices[-24] if len(prices) >= 24 else prices[0]
    move_24h = current - price_24h_ago

    # Volume proxy: use price variance as activity proxy (no per-bar volume from price API)
    recent_24 = prices[-24:]
    week_prior = prices[-168:-24] if len(prices) >= 168 else prices[:-24]

    recent_vol = stdev(recent_24) if len(recent_24) > 1 else 0
    prior_vol = stdev(week_prior) if len(week_prior) > 1 else 0

    volatility_spike = recent_vol / prior_vol if prior_vol > 1e-6 else 1.0

    return {
        "current": current,
        "move_24h": round(move_24h, 4),
        "move_24h_pct": round(move_24h * 100, 2),
        "recent_volatility": round(recent_vol, 4),
        "prior_volatility": round(prior_vol, 4),
        "volatility_spike": round(volatility_spike, 2),
        "n_points": len(prices),
    }


def detect_reflexivity(
    stats: dict,
    imbalance: float,
    sm_active: bool,
    *,
    min_move_pct: float = 5.0,
    min_imbalance: float = 0.15,
    min_vol_spike: float = 1.5,
) -> dict | None:
    """Detect reflexivity: whale entry + amplification loop in motion."""
    move_pct = abs(stats.get("move_24h_pct", 0))
    vol_spike = stats.get("volatility_spike", 1.0)
    current = stats.get("current", 0.5)

    # Require meaningful price move
    if move_pct < min_move_pct:
        return None

    # Require either book imbalance OR smart money activity
    strong_imbalance = abs(imbalance) >= min_imbalance
    if not strong_imbalance and not sm_active:
        return None

    # Require vol spike (activity is accelerating, not decelerating)
    if vol_spike < min_vol_spike:
        return None

    # Direction: follow the move (reflexivity amplifies the direction)
    if stats["move_24h"] > 0:
        signal_side = "YES"
        signal_price = current
    else:
        signal_side = "NO"
        signal_price = 1.0 - current

    # Score: move strength + imbalance + sm bonus
    score = min(move_pct * 2, 40) + min(abs(imbalance) * 60, 30) + (20 if sm_active else 0)
    score = min(score, 100)

    return {
        "bias": "reflexivity",
        "signal_side": signal_side,
        "signal_price": round(signal_price, 4),
        "move_24h_pct": stats["move_24h_pct"],
        "current_price": round(current, 4),
        "book_imbalance": round(imbalance, 3),
        "volatility_spike": vol_spike,
        "sm_active": sm_active,
        "score": round(score, 1),
        "description": (
            f"Prix {stats['move_24h_pct']:+.1f}% en 24h. "
            f"Imbalance book: {imbalance:+.2f}. "
            f"Vol spike: {vol_spike:.1f}×. "
            f"Smart money: {'OUI' if sm_active else 'non'}. "
            f"→ FOLLOW {signal_side} at {signal_price:.3f}."
        ),
    }


async def run() -> int:
    parser = argparse.ArgumentParser(description="SC-012 Reflexivity scanner")
    parser.add_argument("--min-volume", type=float, default=30_000)
    parser.add_argument("--min-move", type=float, default=5.0, help="Min 24h price move %% to trigger")
    parser.add_argument("--min-imbalance", type=float, default=0.15, help="Min book imbalance magnitude [0..1]")
    parser.add_argument("--min-vol-spike", type=float, default=1.5, help="Min volatility spike ratio vs prior week")
    parser.add_argument("--top-markets", type=int, default=80, help="Top N markets by volume to scan")
    parser.add_argument("--top", type=int, default=20, help="Display top N results")
    parser.add_argument("--bankroll", type=float, default=20.0, help="Total bankroll in USD for Kelly sizing")
    parser.add_argument("--from-smart-money", type=Path, default=None,
                        metavar="JSON_FILE",
                        help="Load smart money scan output to boost scores for markets whales touched")
    parser.add_argument("--obsidian", action="store_true")
    parser.add_argument("--json-out", type=Path, default=Path("tmp/reflexivity_signals.json"))
    args = parser.parse_args()

    settings = get_settings()
    today = date.today().isoformat()

    # Load smart money condition_ids for cross-reference
    sm_cids: set[str] = set()
    if args.from_smart_money and args.from_smart_money.exists():
        try:
            sm_data = json.loads(args.from_smart_money.read_text(encoding="utf-8"))
            for entry in sm_data:
                cid = str(entry.get("condition_id") or "")
                if cid:
                    sm_cids.add(cid)
            print(f"  Loaded {len(sm_cids)} condition_ids from smart money scan")
        except Exception as exc:
            print(f"  [!] Could not load smart money JSON: {exc}")

    print(f"\n{'='*70}")
    print(f"SC-012 REFLEXIVITY SCANNER — {today}")
    print(f"Min vol: ${args.min_volume:,.0f} | Top {args.top_markets} | Move >{args.min_move}% | Imbalance >{args.min_imbalance}")
    print(f"{'='*70}")

    all_markets: list[dict] = []
    async with PolymarketClient(settings) as client:
        print("\nFetching high-volume markets...")
        for page in range(10):
            batch = await client.list_markets(active=True, closed=False, limit=500, offset=page * 500)
            if not batch:
                break
            all_markets.extend(batch)

    # Filter binary markets
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
            continue
        candidates.append({
            "condition_id": str(m.get("conditionId") or ""),
            "question": str(m.get("question") or "")[:80],
            "category": str(m.get("category") or ""),
            "volume": vol,
            "token_id": str(token_ids[0]),
            "token_id_no": str(token_ids[1]) if len(token_ids) > 1 else "",
            "current_price": p0,
        })

    candidates.sort(key=lambda x: x["volume"], reverse=True)
    to_scan = candidates[:args.top_markets]
    print(f"  {len(candidates)} binary markets ≥ ${args.min_volume:,.0f} | scanning top {len(to_scan)}")

    signals: list[dict] = []
    start_30d = int(datetime.now(timezone.utc).timestamp() - 30 * 86400)

    async with PolymarketClient(settings) as client:
        for i, market in enumerate(to_scan):
            try:
                # Price history for velocity computation
                history_data = await client.get_price_history(
                    token_id=market["token_id"],
                    start_ts=start_30d,
                    fidelity=60,
                )
                history = history_data.get("history", [])
            except Exception:
                continue

            if len(history) < 48:
                continue

            stats = _price_velocity(history)
            if not stats:
                continue

            # Fetch orderbook for imbalance
            imbalance = 0.0
            try:
                books = await client.get_orderbooks([market["token_id"]])
                if books:
                    book = books[0]
                    bids = book.get("bids") or []
                    asks = book.get("asks") or []
                    imbalance = _compute_book_imbalance(bids, asks)
            except Exception:
                pass

            sm_active = market["condition_id"] in sm_cids

            sig = detect_reflexivity(
                stats,
                imbalance,
                sm_active,
                min_move_pct=args.min_move,
                min_imbalance=args.min_imbalance,
                min_vol_spike=args.min_vol_spike,
            )
            if sig:
                signals.append({**market, **sig, "price_stats": stats})

            if (i + 1) % 10 == 0:
                print(f"  Scanned {i+1}/{len(to_scan)}... ({len(signals)} signals)", end="\r")

    print(f"\n  Done — {len(to_scan)} markets checked, {len(signals)} reflexivity signals")

    # Sort by score desc
    signals.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Compute Kelly sizing from score (score×0.001 = edge estimate, max 10% at score 100)
    for sig in signals:
        sz = size_from_score(
            score=sig.get("score", 0),
            signal_price=sig.get("signal_price", 0.5),
            bankroll=args.bankroll,
        )
        sig["size_usd"] = sz.size_usd
        sig["kelly_full_pct"] = sz.kelly_full_pct

    print(f"\n{'='*122}")
    print(f"{'#':<3} {'Question':<50} {'Side':>4} {'Move%':>6} {'Imbal':>6} {'VolSpike':>9} {'SM':>3} {'Score':>6} {'Size$':>6} {'Vol$M':>7}")
    print(f"{'='*122}")

    for i, sig in enumerate(signals[:args.top], 1):
        sm_flag = "YES" if sig.get("sm_active") else "-"
        size_str = f"${sig['size_usd']:.2f}" if sig["size_usd"] > 0 else "  skip"
        print(
            f"{i:<3} {sig['question'][:50]:<50} "
            f"{sig.get('signal_side', ''):>4} "
            f"{sig.get('move_24h_pct', 0):>+6.1f}% "
            f"{sig.get('book_imbalance', 0):>+6.2f} "
            f"{sig.get('volatility_spike', 1):>8.1f}× "
            f"{sm_flag:>3} "
            f"{sig.get('score', 0):>6.1f} "
            f"{size_str:>6} "
            f"{sig.get('volume', 0)/1e6:>7.2f}M"
        )

    if signals:
        best = signals[0]
        print(f"\n⚡ TOP REFLEXIVITY: [{best['signal_side']}] {best['question'][:65]}")
        print(f"   {best['description']}")
        print(f"   Score: {best['score']:.1f}/100 | Size: ${best['size_usd']:.2f} | Vol: ${best['volume']:,.0f}")
    else:
        print("\nNo reflexivity signals at current thresholds.")
        print("  Try: --min-move 3.0 --min-imbalance 0.10 --min-vol-spike 1.2")

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    clean = [{k: v for k, v in s.items() if k != "price_stats"} for s in signals]
    args.json_out.write_text(json.dumps(clean, indent=2, default=str), encoding="utf-8")
    print(f"\nJSON → {args.json_out}")

    if args.obsidian and signals:
        from polybot.knowledge.obsidian import ObsidianVault
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()

        lines = [
            f"---",
            f"tags: [sc-012, reflexivity, whale-detection, {today}]",
            f"date: {today}",
            f"signals: {len(signals)}",
            f"sm_boosted: {sum(1 for s in signals if s.get('sm_active'))}",
            f"---",
            f"",
            f"# SC-012 Reflexivity — {today}",
            f"",
            f"**Source** : @0xChaseTM 'Iceberg' thread — Réflexivité (Soros)",
            f"**Signaux** : {len(signals)} | **SM actif** : {sum(1 for s in signals if s.get('sm_active'))}",
            f"",
            f"## Logique",
            f"Whale entre → X amplifie → crowd suit → prix monte → edge : entrer tôt, sortir quand volume s'effondre.",
            f"Proxies : imbalance book + spike volatilité 24h vs semaine précédente + smart money cross-ref.",
            f"",
            f"## Signaux",
            f"",
            f"| # | Question | Side | Prix | Move% | Imbal | VolSpike | SM | Score | Vol |",
            f"|---|----------|------|------|-------|-------|----------|----|-------|-----|",
        ]
        for i, s in enumerate(signals[:15], 1):
            sm_f = "OUI" if s.get("sm_active") else "-"
            lines.append(
                f"| {i} | {s['question'][:50]} | {s.get('signal_side')} | "
                f"{s.get('signal_price', 0):.3f} | {s.get('move_24h_pct', 0):+.1f}% | "
                f"{s.get('book_imbalance', 0):+.2f} | {s.get('volatility_spike', 1):.1f}× | "
                f"{sm_f} | {s.get('score', 0):.0f} | ${s.get('volume', 0):,.0f} |"
            )

        lines += [
            f"",
            f"## Règles de sortie",
            f"- Volume/jour retombe sous baseline → loop brisée → exit",
            f"- Prix revient au niveau pré-entrée → stop",
            f"- Smart money vend (détectable via scan_smart_money) → exit",
            f"",
            f"## Warning",
            f"Ce pattern est momentum pur. Sans signal Twitter/X externe, la détection est imparfaite.",
            f"Combiner avec Smart Money scan pour les meilleurs setups.",
            f"",
            f"→ `{args.json_out}`",
        ]

        note_path = vault.write_note(
            "Research/Edge-Research",
            f"SC-012 Reflexivity {today}",
            "\n".join(lines),
            overwrite=True,
        )
        print(f"Obsidian → {note_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
