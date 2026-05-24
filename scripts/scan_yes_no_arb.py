#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SC-014 — YES+NO Arbitrage Scanner.

Detects markets where buying BOTH YES and NO costs less than $1 total.
At resolution one side always pays $1 → guaranteed risk-free profit.

Math:
  Cost = ask_YES + ask_NO
  If Cost < 1.0 - fees → arb gap = 1.0 - Cost - fees
  Win rate documented at 95-98% (near-100% modulo edge-case cancellations)

Source: @0xMovez "buys both sides when YES+NO < $1, locking in $0.02-$0.04 risk-free"
        @0x_Discover research: $39.7M extracted in guaranteed arb (Apr24-Apr25)

Usage:
    PYTHONPATH=src python scripts/scan_yes_no_arb.py
    PYTHONPATH=src python scripts/scan_yes_no_arb.py --min-volume 10000 --min-gap 0.01
    PYTHONPATH=src python scripts/scan_yes_no_arb.py --obsidian --top 30
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
from polybot.research.sizing import quarter_kelly_size

# Polymarket taker fee schedule (max 2%, 0% for some categories)
# Conservative estimate: 1% per leg → 2% total for both sides
DEFAULT_FEE_ESTIMATE = 0.02


def best_ask(orderbook: dict) -> float | None:
    """Return lowest ask price from CLOB orderbook dict."""
    asks = orderbook.get("asks") or []
    if not asks:
        return None
    try:
        return min(float(a["price"]) for a in asks if float(a.get("size", 0)) > 0)
    except (ValueError, KeyError):
        return None


def best_bid(orderbook: dict) -> float | None:
    """Return highest bid price from CLOB orderbook dict."""
    bids = orderbook.get("bids") or []
    if not bids:
        return None
    try:
        return max(float(b["price"]) for b in bids if float(b.get("size", 0)) > 0)
    except (ValueError, KeyError):
        return None


def available_liquidity(orderbook: dict, price_limit: float, side: str = "asks") -> float:
    """Sum of available size at or below (asks) / above (bids) a price threshold."""
    entries = orderbook.get(side) or []
    total = 0.0
    for e in entries:
        try:
            p = float(e["price"])
            s = float(e.get("size", 0))
            if side == "asks" and p <= price_limit:
                total += s
            elif side == "bids" and p >= price_limit:
                total += s
        except (ValueError, KeyError):
            continue
    return total


async def run() -> int:
    parser = argparse.ArgumentParser(description="SC-014 YES+NO Arbitrage Scanner")
    parser.add_argument("--min-volume", type=float, default=5_000, help="Min market volume USD")
    parser.add_argument("--min-gap", type=float, default=0.005, help="Min arb gap after fees (0.5%%)")
    parser.add_argument("--fee-estimate", type=float, default=DEFAULT_FEE_ESTIMATE, help="Total fee estimate for both legs")
    parser.add_argument("--top-markets", type=int, default=200, help="Pre-filter top N markets by volume to scan orderbooks")
    parser.add_argument("--top", type=int, default=20, help="Display top N results")
    parser.add_argument("--bankroll", type=float, default=20.0, help="Bankroll for Kelly sizing")
    parser.add_argument("--obsidian", action="store_true")
    parser.add_argument("--json-out", type=Path, default=Path("tmp/yes_no_arb_signals.json"))
    args = parser.parse_args()

    settings = get_settings()
    today = date.today().isoformat()

    print(f"\n{'='*70}")
    print(f"SC-014 YES+NO ARB SCANNER — {today}")
    print(f"Min vol: ${args.min_volume:,.0f} | Min gap: {args.min_gap:.2%} | Fee est: {args.fee_estimate:.2%}")
    print(f"{'='*70}")

    # ── Step 1: Fetch markets ─────────────────────────────────────────────────
    print("\n[1/3] Fetching active binary markets...")
    all_markets: list[dict] = []
    async with PolymarketClient(settings) as client:
        for page in range(10):
            batch = await client.list_markets(active=True, closed=False, limit=500, offset=page * 500)
            if not batch:
                break
            all_markets.extend(batch)

    # Filter to binary markets above volume threshold
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
        if len(outcomes) != 2 or len(token_ids) < 2:
            continue
        p_yes = float(prices[0]) if prices else 0.5
        p_no = float(prices[1]) if len(prices) > 1 else (1.0 - p_yes)
        # Skip near-resolved markets (they look like arb but fees make it unprofitable)
        if p_yes > 0.96 or p_no > 0.96:
            continue
        mid_sum = p_yes + p_no
        candidates.append({
            "condition_id": str(m.get("conditionId") or ""),
            "question": str(m.get("question") or "")[:80],
            "category": str(m.get("category") or ""),
            "volume": vol,
            "token_id_yes": str(token_ids[0]),
            "token_id_no": str(token_ids[1]),
            "mid_yes": round(p_yes, 4),
            "mid_no": round(p_no, 4),
            "mid_sum": round(mid_sum, 4),
        })

    candidates.sort(key=lambda x: x["volume"], reverse=True)
    to_scan = candidates[:args.top_markets]
    print(f"  {len(candidates)} binary markets ≥ ${args.min_volume:,.0f} | scanning orderbooks for top {len(to_scan)}")

    # ── Step 2: Fetch orderbooks ──────────────────────────────────────────────
    print(f"\n[2/3] Fetching orderbooks ({len(to_scan)} markets × 2 tokens)...")
    signals: list[dict] = []

    async with PolymarketClient(settings) as client:
        for i, m in enumerate(to_scan):
            try:
                book_yes, book_no = await asyncio.gather(
                    client.get_orderbook(m["token_id_yes"]),
                    client.get_orderbook(m["token_id_no"]),
                    return_exceptions=True,
                )
            except Exception:
                continue

            if isinstance(book_yes, Exception) or isinstance(book_no, Exception):
                continue

            ask_yes = best_ask(book_yes)
            ask_no = best_ask(book_no)

            if ask_yes is None or ask_no is None:
                continue

            total_cost = ask_yes + ask_no
            gross_gap = 1.0 - total_cost
            net_gap = gross_gap - args.fee_estimate

            # Liquidity available at these prices
            liq_yes = available_liquidity(book_yes, ask_yes, "asks")
            liq_no = available_liquidity(book_no, ask_no, "asks")
            max_size = min(liq_yes, liq_no)  # can only trade as much as the thinner side
            max_profit = max_size * net_gap

            if net_gap >= args.min_gap:
                signals.append({
                    **m,
                    "ask_yes": round(ask_yes, 4),
                    "ask_no": round(ask_no, 4),
                    "total_cost": round(total_cost, 4),
                    "gross_gap": round(gross_gap, 4),
                    "net_gap": round(net_gap, 4),
                    "liq_yes": round(liq_yes, 2),
                    "liq_no": round(liq_no, 2),
                    "max_size_shares": round(max_size, 2),
                    "max_profit_usd": round(max_profit, 4),
                })

            if (i + 1) % 25 == 0:
                print(f"  Scanned {i+1}/{len(to_scan)}... ({len(signals)} arb signals)", end="\r")

    print(f"\n  Done — {len(to_scan)} markets scanned, {len(signals)} arb opportunities found")

    # ── Step 3: Rank and compute Kelly sizing ─────────────────────────────────
    signals.sort(key=lambda x: x["net_gap"], reverse=True)

    for sig in signals:
        # Edge for Kelly: the gap IS the edge (guaranteed profit per share)
        # Signal price: we're buying at total_cost for $1 payoff → price = total_cost, edge = gap
        sz = quarter_kelly_size(
            edge_decimal=sig["net_gap"],
            signal_price=sig["total_cost"],
            bankroll=args.bankroll,
            book_depth_usd=sig["max_profit_usd"],
        )
        sig["size_usd"] = sz.size_usd
        sig["kelly_full_pct"] = sz.kelly_full_pct

    # ── Output ────────────────────────────────────────────────────────────────
    print(f"\n{'='*130}")
    print(f"{'#':<3} {'Question':<52} {'AskY':>5} {'AskN':>5} {'Gap':>6} {'NetGap':>7} {'Liq':>8} {'MaxP$':>6} {'Size$':>6}")
    print(f"{'='*130}")

    for i, sig in enumerate(signals[:args.top], 1):
        liq_str = f"{min(sig['liq_yes'], sig['liq_no']):.0f}"
        size_str = f"${sig['size_usd']:.2f}" if sig["size_usd"] > 0 else "  skip"
        print(
            f"{i:<3} {sig['question'][:52]:<52} "
            f"{sig['ask_yes']:>5.3f} "
            f"{sig['ask_no']:>5.3f} "
            f"{sig['gross_gap']:>+6.3f} "
            f"{sig['net_gap']:>+6.3f} "
            f"{liq_str:>8} "
            f"${sig['max_profit_usd']:>5.2f} "
            f"{size_str:>6}"
        )

    if signals:
        best = signals[0]
        print(f"\n⭐ BEST ARB: {best['question'][:70]}")
        print(f"   Buy YES @ {best['ask_yes']:.3f} + NO @ {best['ask_no']:.3f} = ${best['total_cost']:.3f} total")
        print(f"   Gross gap: {best['gross_gap']:+.3f} | Net (after {args.fee_estimate:.0%} fee): {best['net_gap']:+.3f}")
        print(f"   Liquidity: {best['liq_yes']:.0f} YES / {best['liq_no']:.0f} NO shares")
        print(f"   Max profit at current depth: ${best['max_profit_usd']:.4f}")
        print(f"   Kelly size: ${best['size_usd']:.2f}")
        print()
        print(f"   Execution: BUY {best['token_id_yes'][:20]}... (YES) + BUY {best['token_id_no'][:20]}... (NO)")
        print(f"   Hold until resolution → collect $1 guaranteed (minus fees)")
    else:
        print(f"\nNo YES+NO arb found at net gap ≥ {args.min_gap:.2%} after {args.fee_estimate:.2%} fees.")
        print(f"Markets are efficiently priced. Try:")
        print(f"  --min-gap 0.001 --fee-estimate 0.01   (if category is fee-free)")
        print(f"  --min-volume 1000                      (include smaller markets)")

    print(f"\nTotal arb signals: {len(signals)} | Best gap: {signals[0]['net_gap']:.3f}" if signals else "")

    # ── Save ──────────────────────────────────────────────────────────────────
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps({
        "date": today,
        "markets_scanned": len(to_scan),
        "signals_found": len(signals),
        "fee_estimate": args.fee_estimate,
        "min_gap": args.min_gap,
        "signals": signals[:50],
    }, indent=2), encoding="utf-8")
    print(f"JSON → {args.json_out}")

    if args.obsidian and signals:
        from polybot.knowledge.obsidian import ObsidianVault
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()
        lines = [
            f"---", f"tags: [sc-014, yes-no-arb, {today}]", f"date: {today}",
            f"signals: {len(signals)}", f"best_gap: {signals[0]['net_gap']:.4f}", f"---", "",
            f"# SC-014 YES+NO Arb — {today}", "",
            f"**Markets scanned**: {len(to_scan)} | **Signals**: {len(signals)} | **Fee assumption**: {args.fee_estimate:.0%}",
            "", "| # | Question | AskY | AskN | Net Gap | Max Profit$ |",
            "|---|----------|------|------|---------|-------------|",
        ]
        for i, s in enumerate(signals[:15], 1):
            lines.append(f"| {i} | {s['question'][:50]} | {s['ask_yes']:.3f} | {s['ask_no']:.3f} | {s['net_gap']:+.3f} | ${s['max_profit_usd']:.4f} |")
        vault.write_note("Research/Edge-Research", f"SC-014 YES+NO Arb {today}", "\n".join(lines), overwrite=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
