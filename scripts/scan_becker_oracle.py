#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Scan active Polymarket markets with Becker calibration + optional Claude oracle.

Usage:
    PYTHONPATH=src python scripts/scan_becker_oracle.py
    PYTHONPATH=src python scripts/scan_becker_oracle.py --live      # fetch fresh from Gamma API
    PYTHONPATH=src python scripts/scan_becker_oracle.py --claude    # requires ANTHROPIC_API_KEY
    PYTHONPATH=src python scripts/scan_becker_oracle.py --min-edge 0.05 --min-volume 20000
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
from pathlib import Path

# Force UTF-8 stdout on Windows to handle non-latin chars in market questions
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from polybot.core.config import get_settings
from polybot.research.signals.becker_oracle import enrich_with_claude, scan_becker
from polybot.research.sizing import quarter_kelly_size


async def fetch_markets_live(settings, min_volume: float, price_low: float, price_high: float, pages: int = 5) -> list[dict]:
    """Fetch current markets directly from Gamma API — no DB required."""
    import json as _json
    from polybot.polymarket.api import PolymarketClient

    rows: list[dict] = []
    async with PolymarketClient(settings) as client:
        for page in range(pages):
            batch = await client.list_markets(
                active=True,
                closed=False,
                enable_order_book=True,
                limit=500,
                offset=page * 500,
            )
            if not batch:
                break
            for m in batch:
                vol = float(m.get("volumeNum") or m.get("volume") or 0)
                if vol < min_volume:
                    continue
                question = str(m.get("question", ""))
                condition_id = str(m.get("conditionId") or m.get("condition_id") or "")
                category = str(m.get("category") or "")
                # Gamma API returns outcomePrices and outcomes as JSON strings
                try:
                    prices = _json.loads(m.get("outcomePrices") or "[]")
                    outcomes = _json.loads(m.get("outcomes") or "[]")
                    token_ids = _json.loads(m.get("clobTokenIds") or "[]")
                except Exception:
                    continue
                for idx, (outcome, price_str) in enumerate(zip(outcomes, prices)):
                    price = float(price_str)
                    if price_low <= price <= price_high:
                        rows.append({
                            "condition_id": condition_id,
                            "question": question,
                            "volume": vol,
                            "category": category,
                            "outcome": str(outcome),
                            "price": price,
                            "asset_id": token_ids[idx] if idx < len(token_ids) else "",
                        })
    return rows


async def fetch_markets(database_url: str, min_volume: float, price_low: float, price_high: float) -> list[dict]:
    from sqlalchemy import text
    from polybot.data.storage.database import create_engine
    from sqlalchemy.ext.asyncio import async_sessionmaker

    engine = create_engine(database_url)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        result = await session.execute(text("""
            SELECT
                m.condition_id,
                m.question,
                m.volume,
                m.category,
                o.name AS outcome,
                o.price,
                o.asset_id
            FROM app.markets m
            JOIN app.market_outcomes o ON o.market_id = m.id
            WHERE m.active = true
              AND m.enable_order_book = true
              AND m.condition_id IS NOT NULL
              AND o.price IS NOT NULL
              AND o.price BETWEEN :price_low AND :price_high
              AND m.volume > :min_volume
            ORDER BY m.volume DESC
        """), {"price_low": price_low, "price_high": price_high, "min_volume": min_volume})
        rows = result.fetchall()
    await engine.dispose()

    return [
        {
            "condition_id": str(row.condition_id),
            "question": str(row.question),
            "volume": float(row.volume or 0),
            "category": str(row.category or ""),
            "outcome": str(row.outcome),
            "price": float(row.price),
            "asset_id": str(row.asset_id or ""),
        }
        for row in rows
    ]


async def run() -> int:
    parser = argparse.ArgumentParser(description="Becker oracle scanner")
    parser.add_argument("--claude", action="store_true", help="Enrich with Claude probability oracle")
    parser.add_argument("--live", action="store_true", help="Fetch fresh markets from Gamma API (skip DB)")
    parser.add_argument("--min-volume", type=float, default=50_000)
    parser.add_argument("--min-edge", type=float, default=0.01)
    parser.add_argument("--min-cl-edge", type=float, default=0.03, help="Min Claude edge to show as actionable (default 3%% — maker fees = 0%%)")
    parser.add_argument("--price-low", type=float, default=0.10)
    parser.add_argument("--price-high", type=float, default=0.40)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--bankroll", type=float, default=20.0, help="Total bankroll in USD for Kelly sizing")
    parser.add_argument("--obsidian", action="store_true", help="Write Obsidian report automatically")
    parser.add_argument("--json-out", type=Path, default=Path("tmp/becker_oracle_scan.json"))
    args = parser.parse_args()

    settings = get_settings()

    source = "Gamma API (live)" if args.live else "DB"
    print(f"\nFetching markets from {source} (price {args.price_low:.0%}–{args.price_high:.0%}, vol >${args.min_volume:,.0f})...")
    if args.live:
        markets = await fetch_markets_live(settings, args.min_volume, args.price_low, args.price_high)
    else:
        markets = await fetch_markets(settings.database_url, args.min_volume, args.price_low, args.price_high)
    print(f"  -> {len(markets)} outcomes fetched from {source}")

    signals = scan_becker(
        markets,
        min_volume=args.min_volume,
        price_low=args.price_low,
        price_high=args.price_high,
        min_becker_edge=args.min_edge,
    )
    print(f"  -> {len(signals)} signals after Becker filter (edge > {args.min_edge:.1%})")

    if args.claude:
        if not settings.anthropic_api_key:
            print("\n  [!] ANTHROPIC_API_KEY not set — skipping Claude enrichment")
        else:
            print(f"\n  Calling Claude oracle on top {min(args.top, len(signals))} signals...")
            signals = enrich_with_claude(
                signals[:args.top],
                api_key=settings.anthropic_api_key,
            )
            print(f"  → Claude enrichment done")

    top = signals[:args.top]

    # Compute dollar sizing for each signal
    for sig in top:
        edge = sig.claude_edge if sig.claude_edge is not None else sig.becker_edge
        price = sig.market_price if sig.recommended_side == "YES" else 1.0 - sig.market_price
        sig._size = quarter_kelly_size(edge_decimal=max(0.0, edge), signal_price=price, bankroll=args.bankroll)

    print(f"\n{'='*100}")
    print(f"{'#':<3} {'Question':<46} {'Price':>6} {'Side':>4} {'BkrEdge':>8} {'ClEdge':>8} {'Kelly¼':>7} {'Size$':>6} {'Vol$M':>6}")
    print(f"{'='*100}")
    for i, sig in enumerate(top, 1):
        claude_edge_str = f"{sig.claude_edge:+.2%}" if sig.claude_edge is not None else "   n/a"
        size_str = f"${sig._size.size_usd:.2f}" if hasattr(sig, '_size') and sig._size.size_usd > 0 else "  skip"
        print(
            f"{i:<3} {sig.question[:46]:<46} "
            f"{sig.market_price:>6.1%} "
            f"{sig.recommended_side:>4} "
            f"{sig.becker_edge:>+8.2%} "
            f"{claude_edge_str:>8} "
            f"{sig.kelly_quarter:>7.2%} "
            f"{size_str:>6} "
            f"{sig.volume_usd/1e6:>6.1f}M"
        )

    if args.claude:
        threshold = args.min_cl_edge
        actionable = [
            s for s in top
            if s.claude_edge is not None and s.claude_edge > threshold and s.claude_confidence in ("medium", "high")
        ]
        near_miss = [
            s for s in top
            if s.claude_edge is not None and s.claude_edge > 0 and s.claude_edge <= threshold and s.recommended_side in ("YES", "NO")
        ]
        if actionable:
            print(f"\n{'='*90}")
            print(f"ACTIONABLE SIGNALS (ClaudeEdge >{threshold:.0%}, confidence medium/high): {len(actionable)}")
            for sig in actionable:
                print(f"\n  [{sig.recommended_side}] {sig.question}")
                size_str = f"${sig._size.size_usd:.2f} ({sig._size.cap_applied})" if hasattr(sig, '_size') else "n/a"
                print(f"       Price={sig.market_price:.2%} | BeckerEdge={sig.becker_edge:+.2%} | ClaudeEdge={sig.claude_edge:+.2%} | Kelly¼={sig.kelly_quarter:.2%} | Size={size_str}")
                print(f"       Confidence={sig.claude_confidence} | Factors: {', '.join(sig.claude_key_factors or [])}")
        else:
            print(f"\nNo signals cleared the {threshold:.0%} Claude-edge threshold at this time.")
        if near_miss:
            print(f"\nNEAR-MISS (positive edge but < {threshold:.0%} or low confidence):")
            for sig in near_miss:
                print(f"  [{sig.recommended_side}] {sig.question[:70]} | ClEdge={sig.claude_edge:+.2%} conf={sig.claude_confidence}")

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    out = []
    for s in top:
        d = s.to_dict()
        if hasattr(s, '_size'):
            d["size_usd"] = s._size.size_usd
            d["kelly_full_pct"] = s._size.kelly_full_pct
            d["size_cap"] = s._size.cap_applied
        out.append(d)
    args.json_out.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nJSON → {args.json_out}")

    if args.obsidian:
        from datetime import date
        from polybot.core.config import get_settings as _get_settings
        from polybot.knowledge.obsidian import ObsidianVault
        _settings = _get_settings()
        vault = ObsidianVault(_settings.obsidian_vault_dir)
        vault.ensure_structure()
        scan_date = date.today().isoformat()
        actionable_ct = len(actionable) if args.claude else 0
        body_lines = [
            f"---",
            f"tags: [oracle, becker, claude, signals, {scan_date}]",
            f"date: {scan_date}",
            f"markets_scanned: {len(markets)}",
            f"signals_becker: {len(signals)}",
            f"actionable_claude: {actionable_ct}",
            f"threshold_cl_edge: {int(args.min_cl_edge * 100)}%",
            f"---",
            f"",
            f"# Oracle Scan — {scan_date}",
            f"",
            f"**Univers** : {len(markets)} outcomes | prix {args.price_low:.0%}–{args.price_high:.0%} | vol >${args.min_volume:,.0f}  ",
            f"**Signaux Becker** : {len(signals)} (edge >{args.min_edge:.0%})  ",
            f"**Signaux actionnables Claude** : {actionable_ct} (edge >{args.min_cl_edge:.0%}, confiance medium+)",
            f"",
        ]
        if args.claude and actionable:
            body_lines.append("## Signaux actionnables")
            for i, sig in enumerate(actionable, 1):
                body_lines.append(f"\n### {i}. {sig.question[:70]} — {sig.recommended_side}")
                body_lines.append(f"- **Prix** : {sig.market_price:.2%} | **ClEdge** : {sig.claude_edge:+.2%} | **Kelly¼** : {sig.kelly_quarter:.2%} | **Vol** : ${sig.volume_usd/1e6:.1f}M")
                body_lines.append(f"- **Confiance** : {sig.claude_confidence}")
                for factor in (sig.claude_key_factors or []):
                    body_lines.append(f"- {factor}")
                body_lines.append(f"- **condition_id** : `{sig.condition_id}`")
        else:
            body_lines.append("## Résultat\n\nAucun signal actionnable aujourd'hui.")
        if args.claude and near_miss:
            body_lines.append("\n## Near-miss (edge positif < seuil)")
            for sig in near_miss:
                body_lines.append(f"- [{sig.recommended_side}] {sig.question[:70]} | ClEdge={sig.claude_edge:+.2%} conf={sig.claude_confidence}")
        body_lines.append(f"\n## Tableau complet\n")
        body_lines.append("| # | Question | Prix | Side | BkrEdge | ClEdge | Kelly¼ | Vol$M |")
        body_lines.append("|---|----------|------|------|---------|--------|--------|-------|")
        for i, sig in enumerate(top, 1):
            cl = f"{sig.claude_edge:+.2%}" if sig.claude_edge is not None else "n/a"
            body_lines.append(f"| {i} | {sig.question[:50]} | {sig.market_price:.1%} | {sig.recommended_side} | {sig.becker_edge:+.2%} | {cl} | {sig.kelly_quarter:.2%} | {sig.volume_usd/1e6:.1f}M |")
        body_lines.append(f"\n→ `{args.json_out}`")
        note_path = vault.write_note(
            "Research/Oracle-Scans",
            f"Oracle Scan {scan_date}",
            "\n".join(body_lines),
            overwrite=True,
        )
        print(f"Obsidian → {note_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
