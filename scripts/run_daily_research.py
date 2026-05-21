#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Daily Research Pipeline — Oracle + Smart Money + Cross-Validation.

Runs Oracle scan and Smart Money scan, cross-references signals,
logs every signal with timestamp for later resolution tracking.

Usage:
    PYTHONPATH=src python scripts/run_daily_research.py
    PYTHONPATH=src python scripts/run_daily_research.py --obsidian --min-volume 20000
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
from datetime import date, datetime
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from polybot.core.config import get_settings
from polybot.polymarket.api import PolymarketClient
from polybot.research.signals.becker_oracle import enrich_with_claude, scan_becker

SIGNAL_LOG = Path("tmp/signal_log.json")


# ── helpers ──────────────────────────────────────────────────────────────────

def load_signal_log() -> list[dict]:
    if SIGNAL_LOG.exists():
        try:
            return json.loads(SIGNAL_LOG.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_signal_log(log: list[dict]) -> None:
    SIGNAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    SIGNAL_LOG.write_text(json.dumps(log, indent=2, default=str), encoding="utf-8")


def append_signals_to_log(signals: list[dict], source: str, log: list[dict]) -> int:
    """Add new signals to the persistent log. Returns count of new entries."""
    existing_keys = {(e["condition_id"], e["scan_date"]) for e in log}
    added = 0
    today = date.today().isoformat()
    for sig in signals:
        key = (sig.get("condition_id", ""), today)
        if key not in existing_keys:
            log.append({
                "condition_id": sig.get("condition_id", ""),
                "question": sig.get("question", "")[:80],
                "side": sig.get("recommended_side", ""),
                "market_price": sig.get("market_price"),
                "claude_edge": sig.get("claude_edge"),
                "claude_confidence": sig.get("claude_confidence"),
                "kelly_quarter": sig.get("kelly_quarter"),
                "volume_usd": sig.get("volume_usd"),
                "source": source,
                "scan_date": today,
                "logged_at": datetime.utcnow().isoformat(),
                "resolved": False,
                "resolution": None,
                "correct": None,
            })
            added += 1
    return added


# ── Oracle scan ───────────────────────────────────────────────────────────────

async def run_oracle(client: PolymarketClient, settings, min_volume: float, top: int) -> tuple[list[dict], list[dict]]:
    """Run Becker + Claude oracle scan. Returns (all_signals, actionable)."""
    import json as _json

    rows: list[dict] = []
    for page in range(5):
        batch = await client.list_markets(active=True, closed=False, limit=500, offset=page * 500)
        if not batch:
            break
        for m in batch:
            vol = float(m.get("volumeNum") or m.get("volume") or 0)
            if vol < min_volume:
                continue
            try:
                prices = _json.loads(m.get("outcomePrices") or "[]")
                outcomes = _json.loads(m.get("outcomes") or "[]")
                token_ids = _json.loads(m.get("clobTokenIds") or "[]")
            except Exception:
                continue
            for idx, (outcome, price_str) in enumerate(zip(outcomes, prices)):
                price = float(price_str)
                if 0.10 <= price <= 0.40:
                    rows.append({
                        "condition_id": str(m.get("conditionId") or ""),
                        "question": str(m.get("question") or ""),
                        "volume": vol,
                        "category": str(m.get("category") or ""),
                        "outcome": str(outcome),
                        "price": price,
                        "asset_id": token_ids[idx] if idx < len(token_ids) else "",
                    })

    if not rows:
        return [], []

    signals = scan_becker(rows, min_volume=min_volume, price_low=0.10, price_high=0.40)
    if not signals:
        return [], []

    if settings.anthropic_api_key:
        signals = enrich_with_claude(signals[:top], api_key=settings.anthropic_api_key)

    actionable = [
        s for s in signals
        if s.claude_edge is not None and s.claude_edge > 0.03 and s.claude_confidence in ("medium", "high")
        and s.recommended_side in ("YES", "NO")
    ]
    return [s.to_dict() for s in signals], [s.to_dict() for s in actionable]


# ── Smart money scan ──────────────────────────────────────────────────────────

WATCHLIST = [
    {"address": "0xe1d6b51521bd4365769199f392f9818661bd907", "label": "HFT-crypto-728k", "tier": "1"},
    {"address": "0xf705fa045201391d9632b7f3cde06a5e24453ca7", "label": "btc-bot-A", "tier": "3"},
    {"address": "0x1979ae6b7e6534de9c4539d0c205e582ca637c9d", "label": "btc-bot-B", "tier": "3"},
]


async def run_smart_money(client: PolymarketClient) -> dict[str, dict]:
    """Fetch positions for all watchlist wallets. Returns {condition_id: {side, exposure, wallets}}."""
    from collections import defaultdict
    from decimal import Decimal

    market_map: dict[str, dict] = defaultdict(lambda: {"wallets": [], "sides": [], "exposure": 0.0, "question": ""})

    for entry in WATCHLIST:
        try:
            positions = await client.get_wallet_positions(entry["address"], limit=500)
        except Exception:
            continue
        for pos in positions:
            if not isinstance(pos, dict):
                continue
            cid = str(pos.get("conditionId") or pos.get("condition_id") or pos.get("market") or "")
            if not cid:
                continue
            question = str(pos.get("title") or pos.get("question") or cid[:40])
            size = float(pos.get("size") or pos.get("currentValue") or 0)
            outcome = str(pos.get("outcome") or "")
            price = float(pos.get("avgPrice") or pos.get("price") or 0)
            exposure = size * price if price > 0 else size

            market_map[cid]["question"] = question
            market_map[cid]["wallets"].append(entry["label"])
            market_map[cid]["sides"].append(outcome.upper())
            market_map[cid]["exposure"] = market_map[cid]["exposure"] + exposure

    return dict(market_map)


# ── Cross-reference ────────────────────────────────────────────────────────────

def conviction_score(oracle_edge: float, smart_money_match: bool, confidence: str) -> float:
    """Combine Oracle edge + smart money confirmation into a 0-100 score."""
    base = min(oracle_edge * 10, 60)  # Oracle edge: max 60 pts (at 6%+ edge)
    conf_bonus = {"high": 20, "medium": 10, "low": 0}.get(confidence or "", 0)
    sm_bonus = 20 if smart_money_match else 0
    return round(base + conf_bonus + sm_bonus, 1)


# ── Main ──────────────────────────────────────────────────────────────────────

async def run() -> int:
    parser = argparse.ArgumentParser(description="Daily research pipeline")
    parser.add_argument("--min-volume", type=float, default=20_000)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--obsidian", action="store_true")
    parser.add_argument("--json-out", type=Path, default=Path("tmp/daily_research.json"))
    args = parser.parse_args()

    settings = get_settings()
    today = date.today().isoformat()
    log = load_signal_log()

    print(f"\n{'='*70}")
    print(f"DAILY RESEARCH — {today}")
    print(f"{'='*70}")

    async with PolymarketClient(settings) as client:
        # ── Step 1: Oracle ────────────────────────────────────────────────────
        print(f"\n[1/3] Oracle Scan (Becker + Claude)...")
        all_signals, actionable = await run_oracle(client, settings, args.min_volume, args.top)
        print(f"      {len(all_signals)} signals | {len(actionable)} actionable (edge >3%)")

        # ── Step 2: Smart Money ───────────────────────────────────────────────
        print(f"\n[2/3] Smart Money Scan ({len(WATCHLIST)} wallets)...")
        sm_map = await run_smart_money(client)
        print(f"      {len(sm_map)} markets with smart money positions")

    # ── Step 3: Cross-reference ───────────────────────────────────────────────
    print(f"\n[3/3] Cross-referencing signals...")
    combined: list[dict] = []
    for sig in actionable:
        cid = sig.get("condition_id", "")
        sm_data = sm_map.get(cid, {})
        sm_wallets = sm_data.get("wallets", [])
        sm_sides = sm_data.get("sides", [])
        sig_side = sig.get("recommended_side", "")
        sm_aligned = any(s == sig_side for s in sm_sides)
        sm_opposed = any(s != sig_side and s in ("YES", "NO") for s in sm_sides)

        score = conviction_score(
            oracle_edge=sig.get("claude_edge") or 0,
            smart_money_match=sm_aligned,
            confidence=sig.get("claude_confidence") or "",
        )

        combined.append({
            **sig,
            "conviction_score": score,
            "sm_aligned": sm_aligned,
            "sm_opposed": sm_opposed,
            "sm_wallets": sm_wallets,
            "sm_exposure": sm_data.get("exposure", 0),
        })

    combined.sort(key=lambda x: x["conviction_score"], reverse=True)

    # ── Output ────────────────────────────────────────────────────────────────
    print(f"\n{'='*90}")
    print(f"{'#':<3} {'Question':<48} {'Side':>4} {'ClEdge':>7} {'SM':>3} {'Score':>6}")
    print(f"{'='*90}")
    for i, sig in enumerate(combined[:15], 1):
        sm_marker = "✓" if sig["sm_aligned"] else ("✗" if sig["sm_opposed"] else " ")
        print(
            f"{i:<3} {sig['question'][:48]:<48} "
            f"{sig['recommended_side']:>4} "
            f"{sig['claude_edge']:>+7.2%} "
            f"{sm_marker:>3} "
            f"{sig['conviction_score']:>5.0f}pt"
        )

    if combined:
        top = combined[0]
        print(f"\n⭐ TOP SIGNAL: [{top['recommended_side']}] {top['question'][:65]}")
        print(f"   Oracle edge: {top['claude_edge']:+.2%} | Confidence: {top['claude_confidence']} | Score: {top['conviction_score']:.0f}/100")
        if top["sm_aligned"]:
            print(f"   Smart money ALIGNED: {', '.join(top['sm_wallets'])}")
        elif top["sm_opposed"]:
            print(f"   ⚠️  Smart money OPPOSED — lower conviction")

    # ── Signal log ────────────────────────────────────────────────────────────
    new_count = append_signals_to_log(combined, "oracle+sm", log)
    save_signal_log(log)
    total_logged = len(log)
    resolved = sum(1 for e in log if e.get("resolved"))
    correct = sum(1 for e in log if e.get("correct") is True)
    accuracy = correct / resolved if resolved else None
    print(f"\n📊 Signal log: {total_logged} total | {new_count} new today | {resolved} resolved | accuracy: {accuracy:.0%}" if accuracy else f"\n📊 Signal log: {total_logged} total | {new_count} new today | {resolved} resolved")

    # ── Save outputs ──────────────────────────────────────────────────────────
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    output = {"date": today, "oracle_signals": all_signals, "actionable": combined, "smart_money_markets": len(sm_map)}
    args.json_out.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(f"\nJSON → {args.json_out}")

    if args.obsidian:
        from polybot.knowledge.obsidian import ObsidianVault
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()
        lines = [
            f"---",
            f"tags: [daily-research, oracle, smart-money, {today}]",
            f"date: {today}",
            f"oracle_actionable: {len(actionable)}",
            f"sm_markets: {len(sm_map)}",
            f"top_conviction: {combined[0]['conviction_score'] if combined else 0}",
            f"---",
            f"",
            f"# Daily Research — {today}",
            f"",
            f"**Oracle** : {len(all_signals)} signaux | {len(actionable)} actionnables  ",
            f"**Smart Money** : {len(sm_map)} marchés avec positions  ",
            f"**Signal log** : {total_logged} total | {resolved} résolus",
            f"",
            f"## Signaux par conviction",
            f"",
            f"| # | Question | Side | ClEdge | SM | Score |",
            f"|---|----------|------|--------|----|-------|",
        ]
        for i, sig in enumerate(combined[:10], 1):
            sm = "✓" if sig["sm_aligned"] else ("✗" if sig["sm_opposed"] else "–")
            lines.append(f"| {i} | {sig['question'][:50]} | {sig['recommended_side']} | {sig['claude_edge']:+.2%} | {sm} | {sig['conviction_score']:.0f} |")
        if combined:
            top = combined[0]
            lines += [
                f"",
                f"## Top signal détaillé",
                f"",
                f"**[{top['recommended_side']}] {top['question'][:70]}**",
                f"- Prix : {top['market_price']:.2%} | Claude edge : {top['claude_edge']:+.2%} | Kelly¼ : {top['kelly_quarter']:.2%}",
                f"- Confiance : {top['claude_confidence']} | Score conviction : {top['conviction_score']:.0f}/100",
            ]
            if top["sm_aligned"]:
                lines.append(f"- Smart money ALIGNÉ : {', '.join(top['sm_wallets'])}")
            for factor in (top.get("claude_key_factors") or []):
                lines.append(f"- {factor}")
            lines.append(f"- `{top['condition_id']}`")
        lines.append(f"\n→ `{args.json_out}`")
        note_path = vault.write_note("Research/Daily-Reports", f"Daily Research {today}", "\n".join(lines), overwrite=True)
        print(f"Obsidian → {note_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
