#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SC-016 — Wallet Confidence Scanner.

Fast-detect scanner for new edges. Pulls /activity + /positions for each seed
wallet, computes a 0-100 confidence score via wallet_scoring module, ranks them,
outputs JSON + Obsidian markdown.

Designed to work on SHORT samples (weeks). Confidence score penalizes small
samples via Wilson lower bounds and split-half persistence tests rather than
requiring 6-12 months of history.

Usage:
    PYTHONPATH=src python scripts/scan_wallet_confidence.py
    PYTHONPATH=src python scripts/scan_wallet_confidence.py --seed 0xABCD... --label new_whale
    PYTHONPATH=src python scripts/scan_wallet_confidence.py --seeds-file resources/wallet_seeds.txt
    PYTHONPATH=src python scripts/scan_wallet_confidence.py
    PYTHONPATH=src python scripts/scan_wallet_confidence.py --no-leaderboard --seed 0xABCD... --label new_whale
    PYTHONPATH=src python scripts/scan_wallet_confidence.py --top 100 --min-confidence 60 --json-out tmp/wallet_scores.json
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from polybot.core.config import get_settings
from polybot.polymarket.api import PolymarketClient
from polybot.research.wallet_discovery import discover_from_holders
from polybot.research.wallet_scoring import (
    WalletScore,
    recompute_independence,
    score_to_dict,
    score_wallet,
)
from polybot.research.wallet_tracking import (
    diff_scans,
    load_latest_prior,
    report_to_markdown,
    save_scan_snapshot,
)

# ── Seed watchlist (curated from threads + known performers) ─────────────────

SEED_WATCHLIST = [
    {"address": "0x44c1dfe43260c94ed4f1d00de2e1f80fb113ebc1", "label": "aenews2",
     "source": "thread:helicerat0x", "hint": "overreaction_fader"},
    {"address": "0x5bffcf561bcae83af680ad600cb99f1184d6ffbe", "label": "YatSen",
     "source": "thread:0x_Discover", "hint": "anchoring_bias"},
    {"address": "0x9d84ce0306f8551e02efef1680475fc0f1dc1344", "label": "ImJustKen",
     "source": "thread:0x_Discover", "hint": "reflexivity"},
    {"address": "0xb40e89677d59665d5188541ad860450a6e2a7cc9", "label": "Poligarch",
     "source": "thread:multiple", "hint": "longshot_fader"},
    {"address": "0xec981ed70ae69c5cbcac08c1ba063e734f6bafcd", "label": "0xheavy888",
     "source": "thread:0x_Discover", "hint": "end_of_event_sports"},
    # NOTE: HFT-crypto-728k addr from thread is 41-chars (truncated). Removed; rely on
    # leaderboard auto-discovery for active HFT wallets.
    {"address": "0xf705fa045201391d9632b7f3cde06a5e24453ca7", "label": "btc-bot-A",
     "source": "discovery", "hint": "btc_directional"},
    {"address": "0x1979ae6b7e6534de9c4539d0c205e582ca637c9d", "label": "btc-bot-B",
     "source": "discovery", "hint": "btc_directional"},
    {"address": "0x8c80d213c0cbad777d06ee3f58f6ca4bc03102c3", "label": "thread-extract-1",
     "source": "thread:multiple", "hint": "unknown"},
    {"address": "0x594edb9112f526fa6a80b8f858a6379c8a2c1c11", "label": "thread-extract-2",
     "source": "thread:multiple", "hint": "unknown"},
]


# ── Fetching ─────────────────────────────────────────────────────────────────

async def fetch_wallet_data(client: PolymarketClient, address: str, *, activity_limit: int = 500) -> tuple[list, list]:
    """Pull /activity?type=TRADE and /positions for one wallet."""
    try:
        activity = await client.get_wallet_activity(address, limit=activity_limit, activity_type="TRADE")
    except Exception as e:
        print(f"  ⚠️  activity fetch failed for {address[:10]}…: {e}")
        activity = []
    try:
        positions = await client.get_wallet_positions(address, limit=500)
    except Exception as e:
        print(f"  ⚠️  positions fetch failed for {address[:10]}…: {e}")
        positions = []
    return activity, positions


async def fetch_leaderboard_seeds(client: PolymarketClient, top_n: int = 50) -> list[dict]:
    """Pull top wallets from Polymarket leaderboard as fresh seeds.

    Queries 7 windows: profit 1d/7d/30d/all + volume 1d/7d/30d.
    A wallet appearing in multiple windows is a stability signal — tracked via
    _source_count after deduplication in dedupe_seeds().
    """
    seeds: list[dict] = []
    url = "https://lb-api.polymarket.com"
    queries = [
        ("/profit", {"window": "1d",  "limit": top_n}, "lb-profit-1d"),
        ("/profit", {"window": "7d",  "limit": top_n}, "lb-profit-7d"),
        ("/profit", {"window": "30d", "limit": top_n}, "lb-profit-30d"),
        ("/profit", {"window": "all", "limit": top_n}, "lb-profit-all"),
        ("/volume", {"window": "1d",  "limit": top_n}, "lb-volume-1d"),
        ("/volume", {"window": "7d",  "limit": top_n}, "lb-volume-7d"),
        ("/volume", {"window": "30d", "limit": top_n}, "lb-volume-30d"),
    ]
    for path, params, tag in queries:
        try:
            data = await client._get(url, path, params=params)
        except Exception as e:
            print(f"  ⚠️  {tag} fetch failed: {e}")
            continue
        if not isinstance(data, list):
            continue
        for entry in data:
            addr = (entry.get("proxyWallet") or entry.get("address") or "").lower()
            if not addr or len(addr) != 42 or not addr.startswith("0x"):
                continue
            name = (entry.get("name") or "").strip() or addr[:10]
            seeds.append({
                "address": addr,
                "label": f"{tag}:{name[:14]}",
                "source": tag,
                "hint": "unknown",
            })
    return seeds


def _is_valid_address(addr: str) -> bool:
    """0x + 40 hex chars."""
    if not addr or len(addr) != 42 or not addr.startswith("0x"):
        return False
    try:
        int(addr[2:], 16)
        return True
    except ValueError:
        return False


def dedupe_seeds(seeds: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    skipped = 0
    for s in seeds:
        addr = s["address"].lower()
        if not _is_valid_address(addr):
            skipped += 1
            continue
        if addr not in seen:
            seen[addr] = dict(s, address=addr, _source_count=1)
        else:
            existing = set(seen[addr]["source"].split(","))
            new_src = s["source"]
            if new_src not in existing:
                seen[addr]["source"] = f"{seen[addr]['source']},{new_src}"
                seen[addr]["_source_count"] = seen[addr].get("_source_count", 1) + 1
    if skipped:
        print(f"   skipped {skipped} invalid addresses")
    # Sort multi-source wallets first so they get scored early
    return sorted(seen.values(), key=lambda s: s.get("_source_count", 1), reverse=True)


# ── Reporting ────────────────────────────────────────────────────────────────

def print_ranked_table(scores: list[WalletScore]) -> None:
    print(f"\n{'='*128}")
    print(f"{'#':<3} {'Badge':<11} {'Label':<22} {'Conf':>5} {'EdgeType':<26} {'Pos':>4} {'Rsl':>4} {'WR':>5} {'ROI_LB%':>8} {'MedHold':>8}")
    print("-" * 128)
    for i, ws in enumerate(scores, 1):
        d = ws.diagnostics
        print(
            f"{i:<3} {ws.risk_badge:<11} {ws.label[:22]:<22} {ws.confidence:>5.1f} "
            f"{ws.edge_type[:26]:<26} {d.n_positions:>4} {d.n_resolved:>4} "
            f"{d.win_rate:>5.0%} {d.roi_wilson_lb_pct:>8.1f} {d.median_hold_hours:>7.1f}h"
        )


def print_top_detail(scores: list[WalletScore], n: int = 5) -> None:
    print(f"\n{'='*120}")
    print(f"TOP {min(n, len(scores))} — Detail")
    print(f"{'='*120}")
    for i, ws in enumerate(scores[:n], 1):
        s = ws.sub_scores
        d = ws.diagnostics
        print(f"\n#{i} {ws.label}  [{ws.risk_badge}]  Confidence: {ws.confidence:.1f}/100")
        print(f"   Address:  {ws.address}")
        print(f"   EdgeType: {ws.edge_type}")
        print(f"   Sub-scores: "
              f"edge={s.edge_proof:.0f} | sample={s.sample_sufficiency:.0f} | "
              f"persist={s.persistence:.0f} | anti-luck={s.anti_luck:.0f} | "
              f"risk={s.risk_taken:.0f} | copy={s.copyability:.0f} | indep={s.independence:.0f}")
        print(f"   Stats: {d.n_resolved} resolved / {d.n_trades} trades | "
              f"PnL ${d.total_pnl_usd:+,.0f} | WinRate {d.win_rate:.0%} (LB {d.win_rate_wilson_lb:.0%}) | "
              f"MaxDD {d.max_drawdown_pct:.1f}%")
        print(f"   Profile: avg entry @ {d.avg_entry_price:.2f} | "
              f"{d.price_regime_split['longshot']:.0%} longshot / "
              f"{d.price_regime_split['midprice']:.0%} mid / "
              f"{d.price_regime_split['favorite']:.0%} favorite | "
              f"main cat: {d.main_category} ({d.category_concentration:.0%})")
        for r in ws.reasons:
            print(f"   • {r}")


def build_obsidian_markdown(scores: list[WalletScore], scan_ts: str, min_conf: float) -> str:
    """Generate Obsidian-flavoured markdown for the scan."""
    qualified = [s for s in scores if s.confidence >= min_conf]
    lines = [
        f"# SC-016 Wallet Confidence Scan — {scan_ts}",
        "",
        f"**Wallets scored:** {len(scores)}",
        f"**Qualified (conf ≥ {min_conf}):** {len(qualified)}",
        f"**Green badges:** {sum(1 for s in scores if '🟢' in s.risk_badge)}",
        f"**Black flags:** {sum(1 for s in scores if '⚫' in s.risk_badge)}",
        "",
        "## Methodology",
        "",
        "Confidence is a weighted blend of 7 sub-scores computed from **on-chain trade history only**:",
        "",
        "- **EDGE_PROOF (25%)** — Wilson lower bound 90% of mean per-trade ROI",
        "- **SAMPLE_SUFFICIENCY (15%)** — Sigmoid penalty for <30 resolved trades",
        "- **PERSISTENCE (15%)** — Split-half stability of ROI",
        "- **ANTI_LUCK (15%)** — Inverse Gini of positive-PnL contributions (penalize jackpot wallets)",
        "- **RISK_TAKEN (10%)** — Max drawdown + position concentration",
        "- **COPYABILITY (10%)** — Median hold time (slow → copyable via PolyCop)",
        "- **INDEPENDENCE (10%)** — v1 placeholder (cross-corr in v2)",
        "",
        "Badge thresholds: 🟢 conf≥75 + n≥40 + persist≥50  |  🟡 partial  |  🔴 conf<50 or n<20  |  ⚫ insider pattern",
        "",
        "## Ranked Wallets",
        "",
        "| # | Badge | Label | Conf | EdgeType | Trd | Rsl | WinRate (LB) | ROI LB% | MedHold | Address |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, ws in enumerate(scores, 1):
        d = ws.diagnostics
        lines.append(
            f"| {i} | {ws.risk_badge} | {ws.label} | {ws.confidence:.1f} | {ws.edge_type} | "
            f"{d.n_trades} | {d.n_resolved} | {d.win_rate:.0%} ({d.win_rate_wilson_lb:.0%}) | "
            f"{d.roi_wilson_lb_pct:+.1f}% | {d.median_hold_hours:.1f}h | `{ws.address}` |"
        )

    lines.extend(["", "## Detail — Qualified Wallets", ""])
    for ws in qualified[:15]:
        s, d = ws.sub_scores, ws.diagnostics
        lines.extend([
            f"### {ws.label}  {ws.risk_badge}  ({ws.confidence:.1f}/100)",
            "",
            f"- **Address**: `{ws.address}`",
            f"- **Edge type**: `{ws.edge_type}`",
            f"- **Sample**: {d.n_resolved} resolved / {d.n_trades} total trades",
            f"- **PnL**: ${d.total_pnl_usd:+,.0f} (realized ${d.realized_pnl_usd:+,.0f})",
            f"- **WinRate**: {d.win_rate:.1%} (Wilson LB: {d.win_rate_wilson_lb:.1%})",
            f"- **ROI**: avg {d.avg_roi_pct:+.1f}% / LB {d.roi_wilson_lb_pct:+.1f}%",
            f"- **Max DD**: {d.max_drawdown_pct:.1f}%  |  **Top position**: {d.top_position_pnl_share:.0%} of PnL",
            f"- **Hold time**: median {d.median_hold_hours:.1f}h  |  **Avg entry**: {d.avg_entry_price:.2f}",
            f"- **Price regime**: {d.price_regime_split['longshot']:.0%} longshot / "
            f"{d.price_regime_split['midprice']:.0%} mid / {d.price_regime_split['favorite']:.0%} favorite",
            f"- **Main category**: {d.main_category} ({d.category_concentration:.0%} concentration)",
            f"- **Sub-scores**: edge={s.edge_proof:.0f} sample={s.sample_sufficiency:.0f} "
            f"persist={s.persistence:.0f} anti-luck={s.anti_luck:.0f} risk={s.risk_taken:.0f} "
            f"copy={s.copyability:.0f} indep={s.independence:.0f}",
            "",
        ])
        if ws.reasons:
            lines.append("**Notes**:")
            for r in ws.reasons:
                lines.append(f"- {r}")
            lines.append("")

    lines.extend([
        "## Next steps",
        "",
        "1. Re-run weekly to catch new wallets and detect edge decay on tracked ones",
        "2. For 🟢 wallets, paper-mirror via PolyCop with 10% bankroll cap and monitor 30 days",
        "3. For 🟡 wallets, watch for sample to grow past n=40 then re-evaluate",
        "4. For ⚫ flags, DO NOT copy — insider edges legally toxic and don't persist after disclosure",
        "",
        "## Links",
        "",
        "- [[scan_smart_follower]] — Real-time entry detection on tracked wallets",
        "- [[strategy_registry]] — Strategy classifications",
        "- [[edge_research_tests]] — Validation framework",
    ])

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

async def run() -> int:
    parser = argparse.ArgumentParser(description="SC-016 Wallet Confidence Scanner")
    parser.add_argument("--seed", action="append", help="Additional wallet address(es)", default=[])
    parser.add_argument("--label", action="append", help="Label(s) matching --seed entries", default=[])
    parser.add_argument("--seeds-file", type=Path, help="File with one address per line (or addr,label)")
    parser.add_argument("--no-leaderboard", action="store_true",
                        help="Skip leaderboard seeds (fetched across 7 windows by default)")
    parser.add_argument("--top", type=int, default=50, help="Top N per leaderboard window (default 50)")
    parser.add_argument("--no-holders", action="store_true",
                        help="Skip holder discovery from top-volume markets (on by default)")
    parser.add_argument("--discover-markets", type=int, default=40,
                        help="How many top markets to crawl for holders")
    parser.add_argument("--discover-min-amount", type=float, default=1_000.0,
                        help="Min share amount for a holder to qualify as seed")
    parser.add_argument("--activity-limit", type=int, default=500, help="Max activity rows per wallet")
    parser.add_argument("--min-confidence", type=float, default=50.0, help="Min confidence for 'qualified' list")
    parser.add_argument("--json-out", type=Path, default=Path("tmp/wallet_confidence.json"))
    parser.add_argument("--obsidian-out", type=Path,
                        default=Path("obsidian-vault/scans/sc-016-wallet-confidence.md"))
    parser.add_argument("--no-obsidian", action="store_true")
    parser.add_argument("--snapshots-dir", type=Path, default=Path("tmp/wallet_scans"),
                        help="Directory for longitudinal scan snapshots")
    parser.add_argument("--no-tracking", action="store_true",
                        help="Skip longitudinal diff vs prior scan")
    parser.add_argument("--changelog-out", type=Path,
                        default=Path("obsidian-vault/scans/sc-016-wallet-changelog.md"))
    args = parser.parse_args()

    # Build seed list
    seeds = list(SEED_WATCHLIST)
    for i, addr in enumerate(args.seed):
        label = args.label[i] if i < len(args.label) else f"cli-seed-{i}"
        seeds.append({"address": addr.lower(), "label": label, "source": "cli", "hint": "unknown"})
    if args.seeds_file and args.seeds_file.exists():
        for line in args.seeds_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            addr = parts[0].lower()
            label = parts[1] if len(parts) > 1 else addr[:10]
            seeds.append({"address": addr, "label": label, "source": "file", "hint": "unknown"})

    settings = get_settings()
    scan_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    async with PolymarketClient(settings) as client:
        if not args.no_leaderboard:
            print(f"[Leaderboard] Fetching top {args.top} × 7 windows (profit 1d/7d/30d/all + volume 1d/7d/30d)…")
            lb_seeds = await fetch_leaderboard_seeds(client, top_n=args.top)
            seeds.extend(lb_seeds)
            print(f"   +{len(lb_seeds)} leaderboard entries (pre-dedup)")

        if not args.no_holders:
            print(f"[Discovery] Crawling holders of top {args.discover_markets} markets…")
            hold_seeds = await discover_from_holders(
                client,
                n_markets=args.discover_markets,
                min_holder_size_usd=args.discover_min_amount,
            )
            seeds.extend(hold_seeds)
            print(f"   +{len(hold_seeds)} holder-discovered entries (pre-dedup)")

        seeds = dedupe_seeds(seeds)
        multi_lb = sum(1 for s in seeds if s.get("_source_count", 1) >= 2)
        print(f"\n{'='*120}")
        print(f"SC-016 WALLET CONFIDENCE — {scan_ts}")
        print(f"Seeds: {len(seeds)} unique wallets  |  {multi_lb} appear in 2+ sources (priority order)")
        print(f"{'='*120}")

        scores: list[WalletScore] = []
        positions_by_addr: dict[str, list[dict]] = {}
        for i, seed in enumerate(seeds, 1):
            print(f"\n[{i}/{len(seeds)}] {seed['label']} ({seed['address'][:10]}…) source={seed['source']}")
            activity, positions = await fetch_wallet_data(client, seed["address"], activity_limit=args.activity_limit)
            print(f"   fetched: {len(activity)} activity rows, {len(positions)} open positions")
            ws = score_wallet(seed["address"], seed["label"], activity, positions)
            print(f"   → confidence {ws.confidence:.1f}  {ws.risk_badge}  edge={ws.edge_type}")
            scores.append(ws)
            positions_by_addr[seed["address"]] = positions

    # Independence v2 post-processing
    scores = recompute_independence(scores, positions_by_addr)
    scores.sort(key=lambda w: w.confidence, reverse=True)

    print_ranked_table(scores)
    print_top_detail(scores, n=5)

    # JSON out + snapshot
    snapshot = {
        "scan_ts": scan_ts,
        "min_confidence": args.min_confidence,
        "n_wallets": len(scores),
        "n_qualified": sum(1 for s in scores if s.confidence >= args.min_confidence),
        "scores": [score_to_dict(s) for s in scores],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"\nJSON  → {args.json_out}")

    # Longitudinal tracking
    if not args.no_tracking:
        prior = load_latest_prior(args.snapshots_dir)
        snap_path = save_scan_snapshot(snapshot, out_dir=args.snapshots_dir)
        print(f"SNAP  → {snap_path}")
        report = diff_scans(snapshot, prior[1] if prior else None)
        if prior:
            print(f"\nTracking vs prior scan ({prior[0].name}):")
            print(f"  🆕 New high-conf: {len(report.new_wallets)}")
            print(f"  ⬆️  Promoted: {len(report.promoted)}")
            print(f"  ⬇️  Demoted: {len(report.demoted)}")
            print(f"  📈 Rising: {len(report.rising)}")
            print(f"  📉 Decaying: {len(report.decaying)}")
            print(f"  💤 Newly inactive: {len(report.newly_inactive)}")
        args.changelog_out.parent.mkdir(parents=True, exist_ok=True)
        args.changelog_out.write_text(report_to_markdown(report), encoding="utf-8")
        print(f"CHG   → {args.changelog_out}")

    # Obsidian out
    if not args.no_obsidian:
        args.obsidian_out.parent.mkdir(parents=True, exist_ok=True)
        md = build_obsidian_markdown(scores, scan_ts, args.min_confidence)
        args.obsidian_out.write_text(md, encoding="utf-8")
        print(f"MD    → {args.obsidian_out}")

    qualified = [s for s in scores if s.confidence >= args.min_confidence]
    green = [s for s in scores if "🟢" in s.risk_badge]
    black = [s for s in scores if "⚫" in s.risk_badge]
    seed_by_addr = {s["address"]: s for s in seeds}
    multi_green = [
        w for w in green
        if seed_by_addr.get(w.address, {}).get("_source_count", 1) >= 2
    ]
    print(f"\nSummary: {len(scores)} scanned → {len(qualified)} qualified ≥ {args.min_confidence} | "
          f"{len(green)} 🟢 GREEN | {len(black)} ⚫ BLACK flags")
    if multi_green:
        print(f"  ★  {len(multi_green)} GREEN wallet(s) confirmed in 2+ leaderboard windows:")
        for w in multi_green:
            src_count = seed_by_addr[w.address].get("_source_count", 1)
            sources = seed_by_addr[w.address].get("source", "")
            print(f"     {w.label}  conf={w.confidence:.1f}  sources={src_count}  [{sources}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
