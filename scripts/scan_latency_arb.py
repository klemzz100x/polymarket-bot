#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SC-013 — Latency Arbitrage Scanner (Binance → Polymarket lag detection).

Monitors BTC/ETH price on Binance and Polymarket crypto markets simultaneously.
Measures the real lag between Binance moves and Polymarket price updates —
confirmed at 2.7s average in Q1 2026 per research threads.

Strategy:
  Binance BTC moves → 2.7s window → Polymarket price lags → place order in direction
  Edge: $496/trade average for top wallet (4,049 trades documented)

Usage:
    PYTHONPATH=src python scripts/scan_latency_arb.py
    PYTHONPATH=src python scripts/scan_latency_arb.py --symbol ETH --duration 120 --min-move 0.003
    PYTHONPATH=src python scripts/scan_latency_arb.py --discover  # only show crypto markets, no monitoring
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from polybot.core.config import get_settings
from polybot.polymarket.api import PolymarketClient

BINANCE_REST = "https://api.binance.com/api/v3"
BINANCE_SYMBOLS = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}


async def get_binance_price(client: httpx.AsyncClient, symbol: str) -> float:
    """Fetch current spot price from Binance REST (public, no auth)."""
    r = await client.get(f"{BINANCE_REST}/ticker/price", params={"symbol": symbol})
    r.raise_for_status()
    return float(r.json()["price"])


async def discover_crypto_markets(poly_client: PolymarketClient, symbol: str, top_n: int = 20) -> list[dict]:
    """Find active Polymarket markets correlated with BTC/ETH price."""
    kw = symbol.upper()
    kw_full = {"BTC": ["BTC", "Bitcoin", "bitcoin"], "ETH": ["ETH", "Ethereum", "ethereum"], "SOL": ["SOL", "Solana"]}.get(kw, [kw])

    markets: list[dict] = []
    for page in range(5):
        batch = await poly_client.list_markets(active=True, closed=False, limit=500, offset=page * 500)
        if not batch:
            break
        markets.extend(batch)

    candidates = []
    for m in markets:
        q = str(m.get("question") or "")
        cat = str(m.get("category") or "").lower()
        if not any(k in q for k in kw_full):
            continue
        try:
            prices = json.loads(m.get("outcomePrices") or "[]")
            outcomes = json.loads(m.get("outcomes") or "[]")
            token_ids = json.loads(m.get("clobTokenIds") or "[]")
        except Exception:
            continue
        if len(outcomes) != 2 or not token_ids:
            continue
        p0 = float(prices[0]) if prices else 0.5
        if p0 < 0.02 or p0 > 0.98:
            continue
        vol = float(m.get("volumeNum") or 0)
        candidates.append({
            "condition_id": str(m.get("conditionId") or ""),
            "question": q[:80],
            "category": cat,
            "volume": vol,
            "token_id_yes": str(token_ids[0]),
            "token_id_no": str(token_ids[1]) if len(token_ids) > 1 else "",
            "price_yes": p0,
            "price_no": float(prices[1]) if len(prices) > 1 else 1 - p0,
            "end_date": str(m.get("endDateIso") or m.get("endDate") or ""),
        })

    candidates.sort(key=lambda x: x["volume"], reverse=True)
    return candidates[:top_n]


async def monitor_polymarket_price(poly_client: PolymarketClient, token_id: str) -> float | None:
    """Fetch current best-bid price for a YES token from the orderbook."""
    try:
        book = await poly_client.get_orderbook(token_id)
        bids = book.get("bids") or []
        if not bids:
            return None
        best_bid = max(float(b["price"]) for b in bids)
        return best_bid
    except Exception:
        return None


async def run() -> int:
    parser = argparse.ArgumentParser(description="SC-013 Latency Arbitrage Scanner")
    parser.add_argument("--symbol", default="BTC", choices=list(BINANCE_SYMBOLS.keys()), help="Crypto to monitor")
    parser.add_argument("--duration", type=int, default=60, help="Monitoring duration in seconds")
    parser.add_argument("--interval", type=float, default=0.5, help="Poll interval in seconds")
    parser.add_argument("--min-move", type=float, default=0.003, help="Min Binance price move to flag (0.3%%)")
    parser.add_argument("--min-lag-gap", type=float, default=0.01, help="Min poly lag vs binance move to signal")
    parser.add_argument("--top-markets", type=int, default=10, help="Max crypto markets to track")
    parser.add_argument("--discover", action="store_true", help="Only discover markets, skip monitoring")
    parser.add_argument("--json-out", type=Path, default=Path("tmp/latency_arb_events.json"))
    args = parser.parse_args()

    settings = get_settings()
    binance_sym = BINANCE_SYMBOLS[args.symbol]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    print(f"\n{'='*70}")
    print(f"SC-013 LATENCY ARB SCANNER — {today}")
    print(f"Symbol: {args.symbol} ({binance_sym}) | Duration: {args.duration}s | Interval: {args.interval}s")
    print(f"{'='*70}")

    async with PolymarketClient(settings) as poly_client:
        # ── Discovery ─────────────────────────────────────────────────────────
        print(f"\n[1/2] Discovering Polymarket {args.symbol} markets...")
        markets = await discover_crypto_markets(poly_client, args.symbol, args.top_markets)
        print(f"      Found {len(markets)} correlated markets\n")

        if not markets:
            print(f"  No active {args.symbol} markets found — try a different symbol or check market status.")
            return 1

        print(f"{'#':<3} {'Question':<60} {'Price':>6} {'Vol$M':>7}")
        print("-" * 80)
        for i, m in enumerate(markets, 1):
            print(f"{i:<3} {m['question'][:60]:<60} {m['price_yes']:>6.3f} {m['volume']/1e6:>7.2f}M")

        if args.discover:
            return 0

        # ── Monitoring ────────────────────────────────────────────────────────
        print(f"\n[2/2] Live monitoring ({args.duration}s)...")
        print(f"      Binance: {binance_sym} | Polymarket: {len(markets)} markets")
        print(f"      Min move: {args.min_move:.1%} | Min lag gap: {args.min_lag_gap:.1%}\n")
        print(f"{'Time':>8} {'Binance':>10} {'Δ Binance':>10} {'Market':^40} {'ΔPoly':>8} {'LAG':>5}")
        print("-" * 88)

    lag_events: list[dict] = []
    binance_price_0: float | None = None
    poly_prices_0: dict[str, float] = {}  # token_id → price
    iteration = 0

    async with httpx.AsyncClient(timeout=5.0) as binance_http:
        async with PolymarketClient(settings) as poly_client:
            start_ts = time.monotonic()
            while time.monotonic() - start_ts < args.duration:
                t0 = time.monotonic()
                ts_label = f"{time.monotonic() - start_ts:>6.1f}s"

                # ── Binance price ─────────────────────────────────────────────
                try:
                    binance_price = await get_binance_price(binance_http, binance_sym)
                except Exception as e:
                    print(f"{ts_label} Binance error: {e}")
                    await asyncio.sleep(args.interval)
                    continue

                binance_move = 0.0
                if binance_price_0 is not None:
                    binance_move = (binance_price - binance_price_0) / binance_price_0

                # ── Polymarket prices ─────────────────────────────────────────
                for m in markets:
                    tid = m["token_id_yes"]
                    try:
                        poly_price = await monitor_polymarket_price(poly_client, tid)
                    except Exception:
                        poly_price = None

                    if poly_price is None:
                        continue

                    poly_move = 0.0
                    if tid in poly_prices_0:
                        poly_move = poly_price - poly_prices_0[tid]

                    # ── Lag detection ─────────────────────────────────────────
                    if (abs(binance_move) >= args.min_move
                            and abs(poly_move) < args.min_lag_gap
                            and binance_price_0 is not None):
                        direction = "↑" if binance_move > 0 else "↓"
                        expected_side = "YES" if binance_move > 0 else "NO"
                        lag_events.append({
                            "ts": time.monotonic() - start_ts,
                            "binance_price": binance_price,
                            "binance_move_pct": round(binance_move * 100, 4),
                            "poly_price": poly_price,
                            "poly_move": round(poly_move, 4),
                            "market": m["question"][:60],
                            "condition_id": m["condition_id"],
                            "token_id": tid,
                            "expected_side": expected_side,
                            "lag_detected": True,
                        })
                        print(
                            f"{ts_label} {binance_price:>10,.2f} {binance_move:>+9.3%} "
                            f"  {m['question'][:40]:<40} {poly_move:>+7.4f} "
                            f"  {direction} LAG ← trade {expected_side}"
                        )
                    elif abs(binance_move) >= args.min_move and abs(poly_move) >= args.min_lag_gap:
                        # Poly caught up
                        print(
                            f"{ts_label} {binance_price:>10,.2f} {binance_move:>+9.3%} "
                            f"  {m['question'][:40]:<40} {poly_move:>+7.4f}  ✓ synced"
                        )

                    poly_prices_0[tid] = poly_price

                binance_price_0 = binance_price
                iteration += 1

                # Status heartbeat every 10 iterations
                if iteration % 10 == 0 and not lag_events:
                    elapsed = time.monotonic() - start_ts
                    print(f"  [{elapsed:.0f}s] Monitoring... {args.symbol}=${binance_price:,.2f} | No lag events yet")

                # Sleep to maintain interval
                elapsed = time.monotonic() - t0
                await asyncio.sleep(max(0.0, args.interval - elapsed))

    # ── Results ───────────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"RESULTS — {len(lag_events)} lag events detected in {args.duration}s")
    print(f"{'='*70}")

    if lag_events:
        avg_binance_move = sum(abs(e["binance_move_pct"]) for e in lag_events) / len(lag_events)
        by_market: dict[str, int] = {}
        for e in lag_events:
            by_market[e["market"][:50]] = by_market.get(e["market"][:50], 0) + 1

        print(f"\n  Avg Binance move at lag detection : {avg_binance_move:.3f}%")
        print(f"  Markets with lag events:")
        for mkt, count in sorted(by_market.items(), key=lambda x: -x[1]):
            print(f"    {count:>3}x  {mkt}")

        print(f"\n  ⭐ SIGNAL: When {args.symbol} moves >{args.min_move:.1%} on Binance,")
        top = lag_events[0]
        print(f"     trade [{top['expected_side']}] on: {top['market'][:60]}")
        print(f"     Before Polymarket catches up (~2.7s window)")
    else:
        print(f"\n  No lag events in this window.")
        print(f"  Possible reasons:")
        print(f"    - {args.symbol} moved < {args.min_move:.1%} during {args.duration}s")
        print(f"    - Markets already priced in recent moves")
        print(f"    - Try: --min-move 0.001 --duration 300")

    print(f"\n  Infrastructure check:")
    print(f"    Binance latency : polling every {args.interval}s (ok for 2.7s window)")
    print(f"    Improvement    : use WebSocket (<50ms) for real execution")
    print(f"    Current setup  : detects lag but needs <500ms to capture it fully")

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps({
        "symbol": args.symbol,
        "duration_s": args.duration,
        "markets_tracked": len(markets),
        "lag_events": len(lag_events),
        "events": lag_events,
        "markets": [{k: v for k, v in m.items() if k not in ("token_id_yes", "token_id_no")} for m in markets],
    }, indent=2), encoding="utf-8")
    print(f"\nJSON → {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
