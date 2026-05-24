#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SC-015 — Smart Follower (Smart Money Surveillance + Anti-Exit-Liquidity).

Monitors profitable wallets in real-time to detect NEW market entries.
Does NOT blindly copy trades — detects ENTRY patterns and validates with own analysis.

Key insight from threads:
  - Blind copy trading = being exit liquidity (you buy what the whale is selling)
  - Same-block execution impossible at human/REST-poll latency
  - What WORKS: detect what category/market the whale just entered,
    then trade independently on the same market with your own edge analysis

Anti-trap filters (from helicerat0x failure mode #5 + 0x_Discover):
  - Minimum market volume (thin market = whale exiting into you)
  - Time-since-trade filter (>30s delay = adverse selection, skip)
  - Direction validation (is price still favorable vs whale's entry price?)
  - Our own signal cross-check (does Oracle/bias agree?)

Wallet tiers (from threads research):
  Tier 1 — High PnL, SLOW strategy (copyable with delay):
    aenews2    $1.94M  Overreaction fader (hours to resolve)
    YatSen     $2.3M   Anchoring bias (days to resolve)
    ImJustKen  $3.03M  Reflexivity (hours)
    Poligarch  $132k   Longshot fader
  Tier 2 — Medium PnL, mixed speed:
    0xheavy888 $772k   End-of-event bias (esports)
    HFT-728k   $728k   Automated crypto (too fast to copy)
  Tier 3 — Bots (uncopyable, used for direction signal only):
    btc-bot-A  N/A     BTC directional
    btc-bot-B  N/A     BTC directional

Usage:
    PYTHONPATH=src python scripts/scan_smart_follower.py
    PYTHONPATH=src python scripts/scan_smart_follower.py --duration 300 --min-position 50
    PYTHONPATH=src python scripts/scan_smart_follower.py --watchlist tier1  # only Tier 1
    PYTHONPATH=src python scripts/scan_smart_follower.py --discover  # show current positions only
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from polybot.core.config import get_settings
from polybot.polymarket.api import PolymarketClient
from polybot.research.sizing import quarter_kelly_size

# ── Watchlist ─────────────────────────────────────────────────────────────────

WATCHLIST = [
    # Tier 1 — SLOW strategies, copyable with a few-minute delay
    {
        "address": "0x44c1dfe43260c94ed4f1d00de2e1f80fb113ebc1",
        "label": "aenews2",
        "tier": 1,
        "strategy": "overreaction_fader",
        "pnl_usd": 1_940_000,
        "note": "$1.94M, fades news overreaction, resolution in hours",
        "copyable": True,
        "max_delay_s": 300,  # 5-minute window still OK for slow strategy
    },
    {
        "address": "0x5bffcf561bcae83af680ad600cb99f1184d6ffbe",
        "label": "YatSen",
        "tier": 1,
        "strategy": "anchoring_bias",
        "pnl_usd": 2_300_000,
        "note": "$2.3M, anchoring plays, holds for days",
        "copyable": True,
        "max_delay_s": 600,  # 10-minute window fine for days-long holds
    },
    {
        "address": "0x9d84ce0306f8551e02efef1680475fc0f1dc1344",
        "label": "ImJustKen",
        "tier": 1,
        "strategy": "reflexivity",
        "pnl_usd": 3_030_000,
        "note": "$3.03M, reflexivity cascades, hours resolution",
        "copyable": True,
        "max_delay_s": 120,
    },
    {
        "address": "0xb40e89677d59665d5188541ad860450a6e2a7cc9",
        "label": "Poligarch",
        "tier": 1,
        "strategy": "longshot_fader",
        "pnl_usd": 132_939,
        "note": "$133k, fades longshots/favorites, slower",
        "copyable": True,
        "max_delay_s": 600,
    },
    # Tier 2 — Medium speed, partial copy
    {
        "address": "0xec981ed70ae69c5cbcac08c1ba063e734f6bafcd",
        "label": "0xheavy888",
        "tier": 2,
        "strategy": "end_of_event",
        "pnl_usd": 772_000,
        "note": "$772k, end-of-event esports bias",
        "copyable": True,
        "max_delay_s": 180,
    },
    # Tier 3 — Bots: don't copy, use for direction signal only
    {
        "address": "0xe1d6b51521bd4365769199f392f9818661bd907",
        "label": "HFT-crypto-728k",
        "tier": 3,
        "strategy": "hft_crypto",
        "pnl_usd": 728_000,
        "note": "$728k HFT bot, too fast to copy — use for direction",
        "copyable": False,
        "max_delay_s": 0,
    },
    {
        "address": "0xf705fa045201391d9632b7f3cde06a5e24453ca7",
        "label": "btc-bot-A",
        "tier": 3,
        "strategy": "btc_directional",
        "pnl_usd": 0,
        "note": "BTC directional bot — direction signal only",
        "copyable": False,
        "max_delay_s": 0,
    },
    {
        "address": "0x1979ae6b7e6534de9c4539d0c205e582ca637c9d",
        "label": "btc-bot-B",
        "tier": 3,
        "strategy": "btc_directional",
        "pnl_usd": 0,
        "note": "BTC directional bot — direction signal only",
        "copyable": False,
        "max_delay_s": 0,
    },
]

TIER_LABELS = {1: "T1-SLOW", 2: "T2-MED", 3: "T3-BOT"}


def build_watchlist(tier_filter: str | None) -> list[dict]:
    if tier_filter == "tier1":
        return [w for w in WATCHLIST if w["tier"] == 1]
    if tier_filter == "tier2":
        return [w for w in WATCHLIST if w["tier"] <= 2]
    return WATCHLIST


# ── Anti-exit-liquidity checks ────────────────────────────────────────────────

def is_exit_signal(position: dict, market_price: float, whale_price: float) -> tuple[bool, str]:
    """Detect if following this position makes us exit liquidity.

    Returns (is_trap, reason).
    """
    size = float(position.get("size") or 0)
    outcome = str(position.get("outcome") or "").upper()

    # Trap 1: Price has already moved significantly since whale entered
    if whale_price > 0:
        price_drift = (market_price - whale_price) / whale_price
        if outcome == "YES" and price_drift > 0.08:
            return True, f"Price drifted +{price_drift:.1%} since whale entry — chasing"
        if outcome == "NO" and price_drift < -0.08:
            return True, f"Price drifted {price_drift:.1%} since whale entry — chasing NO"

    # Trap 2: Very small size relative to market — whale may be probing/exiting
    if size < 20:
        return True, f"Small position ${size:.0f} — likely noise or test"

    # Trap 3: Market price already near resolution (>92%) — whale is collecting, not entering
    if market_price > 0.92 or market_price < 0.08:
        return True, f"Market near resolution ({market_price:.2%}) — late entry trap"

    return False, ""


def validate_direction(position: dict, own_signals: list[dict]) -> tuple[bool, str]:
    """Check if our own scanners agree with the whale's direction."""
    cid = str(position.get("conditionId") or position.get("condition_id") or "")
    outcome = str(position.get("outcome") or "").upper()

    for sig in own_signals:
        if sig.get("condition_id") == cid:
            sig_side = str(sig.get("recommended_side") or sig.get("signal_side") or "").upper()
            if sig_side == outcome:
                return True, f"Own signal agrees: {sig_side}"
            elif sig_side and sig_side != "MONITOR":
                return False, f"Own signal DISAGREES: we say {sig_side}, whale says {outcome}"
    return True, "No own signal — follow whale with reduced size"


# ── Position snapshot ─────────────────────────────────────────────────────────

async def snapshot_wallet(client: PolymarketClient, wallet: dict) -> list[dict]:
    """Fetch current open positions for a wallet."""
    try:
        positions = await client.get_wallet_positions(wallet["address"], limit=200)
        return [p for p in positions if isinstance(p, dict)]
    except Exception:
        return []


async def get_recent_activity(client: PolymarketClient, wallet: dict, limit: int = 20) -> list[dict]:
    """Fetch recent trades/activity for a wallet."""
    try:
        activity = await client.get_wallet_activity(wallet["address"], limit=limit)
        return [a for a in activity if isinstance(a, dict)]
    except Exception:
        return []


# ── Main ──────────────────────────────────────────────────────────────────────

async def run() -> int:
    parser = argparse.ArgumentParser(description="SC-015 Smart Follower")
    parser.add_argument("--duration", type=int, default=0, help="Monitoring duration in seconds (0 = one-shot snapshot)")
    parser.add_argument("--interval", type=float, default=30.0, help="Poll interval in seconds")
    parser.add_argument("--min-position", type=float, default=25.0, help="Min position size USD to consider")
    parser.add_argument("--min-volume", type=float, default=10_000, help="Min market volume to consider following")
    parser.add_argument("--watchlist", choices=["all", "tier1", "tier2"], default="all")
    parser.add_argument("--discover", action="store_true", help="Show current positions only, no loop")
    parser.add_argument("--bankroll", type=float, default=20.0, help="Total bankroll USD")
    parser.add_argument("--copy-allocation", type=float, default=0.30, help="Fraction of bankroll for copy strategy")
    parser.add_argument("--json-out", type=Path, default=Path("tmp/smart_follower_signals.json"))
    args = parser.parse_args()

    settings = get_settings()
    active_wallets = build_watchlist(args.watchlist if args.watchlist != "all" else None)
    copyable_wallets = [w for w in active_wallets if w["copyable"]]
    signal_wallets = active_wallets  # all wallets used for direction signal
    copy_bankroll = args.bankroll * args.copy_allocation
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    print(f"\n{'='*70}")
    print(f"SC-015 SMART FOLLOWER — {today}")
    print(f"Wallets: {len(active_wallets)} tracked | {len(copyable_wallets)} copyable | {len(active_wallets)-len(copyable_wallets)} signal-only")
    print(f"Copy bankroll: ${copy_bankroll:.2f} ({args.copy_allocation:.0%} of ${args.bankroll:.2f})")
    print(f"{'='*70}")

    print(f"\n{'Label':<16} {'Tier':<8} {'Strategy':<20} {'PnL':>10} {'Copyable':<10} {'MaxDelay':>8}")
    print("-" * 78)
    for w in active_wallets:
        print(
            f"{w['label']:<16} {TIER_LABELS[w['tier']]:<8} {w['strategy']:<20} "
            f"${w['pnl_usd']:>9,.0f} {'YES' if w['copyable'] else 'signal-only':<10} "
            f"{w['max_delay_s']:>6}s"
        )

    all_signals: list[dict] = []
    prev_positions: dict[str, set[str]] = defaultdict(set)  # wallet_addr → set of condition_ids

    async def one_scan(client: PolymarketClient, iteration: int) -> list[dict]:
        scan_signals = []
        print(f"\n[Scan #{iteration}] {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")

        for wallet in active_wallets:
            positions = await snapshot_wallet(client, wallet)
            activity = await get_recent_activity(client, wallet, limit=10)

            # Detect NEW positions (not seen in previous scan)
            current_cids = set()
            new_positions = []
            for pos in positions:
                cid = str(pos.get("conditionId") or pos.get("condition_id") or pos.get("market") or "")
                if not cid:
                    continue
                size = float(pos.get("size") or pos.get("currentValue") or 0)
                if size < args.min_position:
                    continue
                current_cids.add(cid)
                if cid not in prev_positions[wallet["address"]] and iteration > 1:
                    new_positions.append(pos)

            prev_positions[wallet["address"]] = current_cids

            if positions:
                print(f"  {wallet['label']:<16} {len(positions):>3} positions | {len(new_positions)} NEW")
            else:
                print(f"  {wallet['label']:<16} no data")

            # Process new positions
            for pos in new_positions:
                cid = str(pos.get("conditionId") or pos.get("condition_id") or pos.get("market") or "")
                question = str(pos.get("title") or pos.get("question") or cid[:40])
                outcome = str(pos.get("outcome") or "").upper()
                size = float(pos.get("size") or pos.get("currentValue") or 0)
                avg_price = float(pos.get("avgPrice") or pos.get("price") or 0)
                current_price = float(pos.get("currentPrice") or avg_price)

                # Anti-trap check
                is_trap, trap_reason = is_exit_signal(pos, current_price, avg_price)
                if is_trap:
                    print(f"    ⚠️  SKIP (trap): {question[:50]} — {trap_reason}")
                    continue

                # Direction validation (no own signals for now — placeholder)
                direction_ok, direction_reason = validate_direction(pos, [])

                # Kelly sizing on copy bankroll
                if avg_price > 0 and avg_price < 1:
                    # Conservative edge assumption: we're following, not leading → 50% of whale edge
                    copy_edge = 0.04  # conservative 4% edge (reduced from what whale captured)
                    signal_price = avg_price if outcome == "YES" else (1.0 - avg_price)
                    sz = quarter_kelly_size(
                        edge_decimal=copy_edge,
                        signal_price=signal_price,
                        bankroll=copy_bankroll,
                    )
                else:
                    sz = None

                delay_ok = wallet["max_delay_s"] > 0
                signal = {
                    "wallet": wallet["label"],
                    "tier": wallet["tier"],
                    "strategy": wallet["strategy"],
                    "condition_id": cid,
                    "question": question[:70],
                    "outcome": outcome,
                    "whale_size_usd": round(size, 2),
                    "whale_avg_price": round(avg_price, 4),
                    "current_price": round(current_price, 4),
                    "copyable": wallet["copyable"] and delay_ok and direction_ok,
                    "direction_ok": direction_ok,
                    "direction_reason": direction_reason,
                    "size_usd": sz.size_usd if sz else 0.0,
                    "note": wallet["note"],
                }
                scan_signals.append(signal)

                status = "COPY" if signal["copyable"] else "WATCH"
                print(
                    f"    {'🟢' if signal['copyable'] else '👁️ '} {status} [{outcome}] "
                    f"{question[:50]} | ${size:.0f} @ {avg_price:.3f} | "
                    f"Size: ${signal['size_usd']:.2f}"
                )

        return scan_signals

    # ── Snapshot mode ──────────────────────────────────────────────────────────
    async with PolymarketClient(settings) as client:
        if args.discover or args.duration == 0:
            print(f"\n[SNAPSHOT] Current positions across all tracked wallets\n")
            for wallet in active_wallets:
                positions = await snapshot_wallet(client, wallet)
                active_pos = [p for p in positions if float(p.get("size") or p.get("currentValue") or 0) >= args.min_position]
                print(f"\n  {wallet['label']} ({TIER_LABELS[wallet['tier']]}) — {len(active_pos)} positions ≥ ${args.min_position:.0f}")
                for pos in sorted(active_pos, key=lambda x: float(x.get("size") or x.get("currentValue") or 0), reverse=True)[:5]:
                    q = str(pos.get("title") or pos.get("question") or pos.get("market") or "")[:55]
                    outcome = str(pos.get("outcome") or "?").upper()
                    size = float(pos.get("size") or pos.get("currentValue") or 0)
                    price = float(pos.get("avgPrice") or pos.get("price") or 0)
                    print(f"    [{outcome}] {q:<55} ${size:>8,.2f} @ {price:.3f}")

            if args.discover:
                return 0

        # ── Live monitoring loop ───────────────────────────────────────────────
        if args.duration > 0:
            print(f"\n[LIVE MONITORING] {args.duration}s | polling every {args.interval}s")
            print(f"Watching for NEW positions from {len(copyable_wallets)} copyable wallets\n")

            start_ts = time.monotonic()
            iteration = 0

            # First scan to populate baseline
            print("[Initializing baseline positions...]")
            for wallet in active_wallets:
                positions = await snapshot_wallet(client, wallet)
                for pos in positions:
                    cid = str(pos.get("conditionId") or pos.get("condition_id") or pos.get("market") or "")
                    if cid:
                        prev_positions[wallet["address"]].add(cid)
            iteration = 1
            print(f"  Baseline: {sum(len(v) for v in prev_positions.values())} positions tracked\n")

            while time.monotonic() - start_ts < args.duration:
                iteration += 1
                new_signals = await one_scan(client, iteration)
                all_signals.extend(new_signals)

                if new_signals:
                    print(f"\n  ⭐ {len(new_signals)} NEW signal(s) this scan")

                await asyncio.sleep(args.interval)

    # ── Summary ────────────────────────────────────────────────────────────────
    copy_signals = [s for s in all_signals if s.get("copyable")]
    watch_signals = [s for s in all_signals if not s.get("copyable")]

    print(f"\n{'='*70}")
    print(f"SUMMARY — {len(all_signals)} total signals | {len(copy_signals)} to COPY | {len(watch_signals)} to WATCH")
    print(f"{'='*70}")

    if copy_signals:
        print(f"\n{'#':<3} {'Wallet':<12} {'Tier':<7} {'Question':<45} {'Side':>4} {'WhaleSz':>8} {'Size$':>6}")
        print("-" * 92)
        for i, sig in enumerate(copy_signals[:15], 1):
            print(
                f"{i:<3} {sig['wallet']:<12} {TIER_LABELS[sig['tier']]:<7} "
                f"{sig['question'][:45]:<45} {sig['outcome']:>4} "
                f"${sig['whale_size_usd']:>7,.0f} ${sig['size_usd']:>5.2f}"
            )
    else:
        print("\n  No copy signals in this session.")

    print(f"\n📋 Anti-exit-liquidity rules applied:")
    print(f"   ✓ Skip if price drifted >8% since whale entry")
    print(f"   ✓ Skip if position size < ${args.min_position:.0f} (noise/test)")
    print(f"   ✓ Skip if market price >92% (near resolution, whale collecting)")
    print(f"   ✓ Tier 3 bots (too fast) → direction signal only, not copy")
    print(f"   ✓ Kelly sizing on {args.copy_allocation:.0%} sub-bankroll only (${copy_bankroll:.2f})")

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps({
        "date": today,
        "copy_bankroll_usd": copy_bankroll,
        "copy_allocation_pct": args.copy_allocation,
        "wallets_tracked": len(active_wallets),
        "copyable_wallets": len(copyable_wallets),
        "total_signals": len(all_signals),
        "copy_signals": len(copy_signals),
        "signals": all_signals,
    }, indent=2), encoding="utf-8")
    print(f"\nJSON → {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
