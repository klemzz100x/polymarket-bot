#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""BTC Cross-Market Lag Scanner.

Exploits the repricing delay between Binance BTC moves and Polymarket BTC 5-min markets.
When BTC moves ≥0.3% on Binance, Polymarket markets often haven't repriced yet — edge window.

Usage:
    PYTHONPATH=src python scripts/scan_btc_lag.py
    PYTHONPATH=src python scripts/scan_btc_lag.py --duration 120 --interval 3
    PYTHONPATH=src python scripts/scan_btc_lag.py --discover-markets   # list active BTC markets
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from polybot.core.compat import UTC
from polybot.core.config import get_settings
from polybot.polymarket.api import PolymarketClient
from polybot.strategies.latency_arbitrage import BinancePriceTracker, LatencyArbitrageDetector


import re as _re

# Whole-word regex patterns — avoids "Netherlands" matching "eth"
_CRYPTO_PATTERNS = [
    _re.compile(r'\bbitcoin\b', _re.I),
    _re.compile(r'\bbtc\b', _re.I),
    _re.compile(r'\bethereum\b', _re.I),
    _re.compile(r'\bether\b', _re.I),
    _re.compile(r'\bsolana\b', _re.I),
]


def _is_crypto_market(question: str) -> bool:
    return any(p.search(question) for p in _CRYPTO_PATTERNS)


async def discover_btc_markets(client: PolymarketClient, min_volume: float = 10_000) -> list[dict]:
    """Fetch active BTC/crypto short-term markets from Gamma API."""
    import json as _json

    markets = []
    for page in range(5):
        batch = await client.list_markets(active=True, closed=False, limit=500, offset=page * 500)
        if not batch:
            break
        for m in batch:
            question = str(m.get("question") or "").lower()
            vol = float(m.get("volumeNum") or m.get("volume") or 0)
            if vol < min_volume:
                continue
            if not _is_crypto_market(question):
                continue
            try:
                prices = _json.loads(m.get("outcomePrices") or "[]")
                outcomes = _json.loads(m.get("outcomes") or "[]")
                token_ids = _json.loads(m.get("clobTokenIds") or "[]")
            except Exception:
                continue
            if len(token_ids) < 2:
                continue
            # Skip already-resolved markets (price > 0.95 or < 0.05)
            if prices and len(prices) >= 2:
                try:
                    p0, p1 = float(prices[0]), float(prices[1])
                    if min(p0, p1) < 0.03:
                        continue
                except Exception:
                    pass
            markets.append({
                "condition_id": str(m.get("conditionId") or ""),
                "question": str(m.get("question") or "")[:70],
                "volume": vol,
                "outcomes": outcomes,
                "token_ids": token_ids,
                "prices": [float(p) for p in prices] if prices else [],
            })

    return sorted(markets, key=lambda m: m["volume"], reverse=True)


async def run_scan(
    client: PolymarketClient,
    markets: list[dict],
    *,
    duration: int,
    interval: float,
    min_edge_pct: float,
) -> list[dict]:
    """Poll Binance + Polymarket orderbooks for lag signals."""
    from polybot.data.normalization import normalize_orderbook

    detector = LatencyArbitrageDetector()
    signals: list[dict] = []
    end_time = datetime.now(UTC).timestamp() + duration
    tick = 0

    print(f"\nScanning {len(markets)} BTC markets for {duration}s (interval {interval}s)...")
    print(f"Min edge threshold: {min_edge_pct}%")
    print(f"{'─'*70}")

    while datetime.now(UTC).timestamp() < end_time:
        tick += 1
        try:
            btc = await detector.update_price()
            change = detector.price_tracker.get_price_change()
            change_pct = float(change.change_pct) if change else 0.0

            if tick % 5 == 1:  # Print status every 5 ticks
                direction = "▲" if change_pct > 0 else ("▼" if change_pct < 0 else "─")
                print(f"  BTC ${float(btc.price):,.0f} {direction}{abs(change_pct):.3f}%  ({tick} ticks)", end="\r")

            if change and abs(change.change_pct) >= Decimal("0.3"):
                # BTC moved — check all markets for lag
                for market in markets:
                    token_ids = market["token_ids"]
                    if len(token_ids) < 2:
                        continue
                    try:
                        books = await client.get_orderbooks(token_ids[:2])
                        for book in books:
                            snapshot = normalize_orderbook(book, received_at=datetime.now(UTC))
                            sig = detector.detect_signal(
                                snapshot=snapshot,
                                market_id=market["condition_id"],
                                up_asset_id=token_ids[0],
                                down_asset_id=token_ids[1],
                            )
                            if sig and float(sig.edge_pct) >= min_edge_pct:
                                signal_dict = {
                                    "timestamp": sig.timestamp.isoformat(),
                                    "question": market["question"],
                                    "condition_id": market["condition_id"],
                                    "direction": sig.direction,
                                    "btc_change_pct": float(sig.binance_change_pct),
                                    "fair_prob": float(sig.fair_probability),
                                    "market_prob": float(sig.market_probability),
                                    "edge_pct": float(sig.edge_pct),
                                    "confidence": float(sig.confidence),
                                    "volume": market["volume"],
                                }
                                signals.append(signal_dict)
                                print(f"\n  ⚡ SIGNAL [{sig.direction.upper()}] {market['question'][:55]}")
                                print(f"     BTC Δ={change_pct:+.3f}% | Edge={float(sig.edge_pct):.1f}% | Conf={float(sig.confidence):.0%}")
                    except Exception:
                        pass

        except Exception as exc:
            print(f"\n  [!] error: {exc}", end="\r")

        await asyncio.sleep(interval)

    return signals


async def run() -> int:
    parser = argparse.ArgumentParser(description="BTC cross-market lag scanner")
    parser.add_argument("--discover-markets", action="store_true", help="List active BTC markets and exit")
    parser.add_argument("--duration", type=int, default=60, help="Scan duration in seconds")
    parser.add_argument("--interval", type=float, default=5.0, help="Poll interval in seconds")
    parser.add_argument("--min-edge", type=float, default=5.0, help="Min edge %% to report")
    parser.add_argument("--min-volume", type=float, default=10_000)
    parser.add_argument("--json-out", type=Path, default=Path("tmp/btc_lag_signals.json"))
    args = parser.parse_args()

    settings = get_settings()

    async with PolymarketClient(settings) as client:
        print(f"\nDiscovering active BTC markets (vol >${args.min_volume:,.0f})...")
        markets = await discover_btc_markets(client, min_volume=args.min_volume)
        print(f"  -> {len(markets)} BTC markets found")

        if not markets:
            print("No active BTC markets with orderbooks. Nothing to scan.")
            return 0

        print(f"\n{'='*75}")
        print(f"{'#':<3} {'Question':<58} {'Vol$M':>7}")
        print(f"{'='*75}")
        for i, m in enumerate(markets[:10], 1):
            print(f"{i:<3} {m['question']:<58} {m['volume']/1e6:>7.1f}M")

        if args.discover_markets:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(markets, indent=2), encoding="utf-8")
            print(f"\nJSON → {args.json_out}")
            return 0

        signals = await run_scan(
            client,
            markets,
            duration=args.duration,
            interval=args.interval,
            min_edge_pct=args.min_edge,
        )

    print(f"\n\n{'='*75}")
    print(f"Scan complete. Signals detected: {len(signals)}")
    if signals:
        print(f"\n{'#':<3} {'Question':<50} {'Dir':>4} {'BTC Δ':>6} {'Edge%':>6}")
        print(f"{'─'*75}")
        for i, s in enumerate(signals, 1):
            print(f"{i:<3} {s['question'][:50]:<50} {s['direction']:>4} {s['btc_change_pct']:>+6.3f}% {s['edge_pct']:>5.1f}%")
    else:
        print("No actionable lag signals detected in this window.")
        print("Try: longer --duration, lower --min-edge, or wait for BTC volatility.")

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(signals, indent=2, default=str), encoding="utf-8")
    print(f"\nJSON → {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
