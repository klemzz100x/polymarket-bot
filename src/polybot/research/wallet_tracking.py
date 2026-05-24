"""SC-016 — Wallet longitudinal tracking.

Persists scan snapshots and computes deltas between runs:
  - New wallets entering 🟢/🟡 tier
  - Wallets decaying (confidence drop > threshold)
  - Wallets newly inactive (last_trade_age_days jumped)
  - Score trends per wallet across N scans

Snapshots live as JSON files in tmp/wallet_scans/.
On each new scan, we load the most recent prior scan and diff.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WalletDelta:
    address: str
    label: str
    prev_confidence: float | None  # None if new wallet
    new_confidence: float
    delta_confidence: float  # 0 if new
    prev_badge: str | None
    new_badge: str
    badge_changed: bool
    is_new: bool
    is_inactive: bool  # last_trade_age_days > 14
    edge_type: str
    n_resolved: int
    notable_reason: str  # short summary of why this delta matters


@dataclass(frozen=True)
class TrackingReport:
    scan_ts: str
    prev_scan_ts: str | None
    n_current: int
    n_previous: int
    new_wallets: list[WalletDelta]
    promoted: list[WalletDelta]  # badge upgrade (RED→YELLOW, YELLOW→GREEN, etc.)
    demoted: list[WalletDelta]  # badge downgrade
    decaying: list[WalletDelta]  # confidence -10+ but same badge
    rising: list[WalletDelta]    # confidence +10+ but same badge
    newly_inactive: list[WalletDelta]
    all_deltas: list[WalletDelta]


BADGE_RANK = {"⚫ BLACK": -1, "🔴 RED": 0, "🟡 YELLOW": 1, "🟢 GREEN": 2}


def _badge_rank(b: str) -> int:
    return BADGE_RANK.get(b, 0)


def save_scan_snapshot(snapshot: dict, *, out_dir: Path) -> Path:
    """Save a scan snapshot timestamped. Returns path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"scan_{ts}.json"
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return path


def load_latest_prior(out_dir: Path, *, exclude_path: Path | None = None) -> tuple[Path, dict] | None:
    """Load the most recent prior scan, excluding the just-written one."""
    if not out_dir.exists():
        return None
    files = sorted(out_dir.glob("scan_*.json"))
    if exclude_path:
        files = [f for f in files if f != exclude_path]
    if not files:
        return None
    latest = files[-1]
    try:
        return latest, json.loads(latest.read_text(encoding="utf-8"))
    except Exception:
        return None


def diff_scans(current: dict, previous: dict | None) -> TrackingReport:
    """Compute deltas between current and previous scan."""
    cur_by_addr: dict[str, dict] = {s["address"]: s for s in current.get("scores", [])}
    prev_by_addr: dict[str, dict] = {
        s["address"]: s for s in (previous.get("scores", []) if previous else [])
    }

    all_deltas: list[WalletDelta] = []
    new_wallets: list[WalletDelta] = []
    promoted: list[WalletDelta] = []
    demoted: list[WalletDelta] = []
    decaying: list[WalletDelta] = []
    rising: list[WalletDelta] = []
    newly_inactive: list[WalletDelta] = []

    for addr, cur in cur_by_addr.items():
        prev = prev_by_addr.get(addr)
        new_conf = float(cur.get("confidence") or 0)
        new_badge = cur.get("risk_badge") or "🔴 RED"
        is_new = prev is None
        prev_conf = float(prev.get("confidence")) if prev else None
        prev_badge = prev.get("risk_badge") if prev else None
        delta_conf = new_conf - prev_conf if prev_conf is not None else 0.0
        badge_changed = (prev_badge is not None and prev_badge != new_badge)

        diag = cur.get("diagnostics", {})
        inactive_now = float(diag.get("last_trade_age_days") or 0) > 14
        inactive_before = (
            float(prev.get("diagnostics", {}).get("last_trade_age_days") or 0) > 14
            if prev else False
        )

        # Notable reason: pick the highest-priority signal
        reason = ""
        if is_new and new_conf >= 60:
            reason = f"NEW high-confidence wallet ({new_conf:.0f})"
        elif badge_changed and _badge_rank(new_badge) > _badge_rank(prev_badge or ""):
            reason = f"PROMOTED: {prev_badge} → {new_badge}"
        elif badge_changed and _badge_rank(new_badge) < _badge_rank(prev_badge or ""):
            reason = f"DEMOTED: {prev_badge} → {new_badge}"
        elif delta_conf <= -10:
            reason = f"DECAYING: {delta_conf:+.1f} confidence"
        elif delta_conf >= 10:
            reason = f"RISING: {delta_conf:+.1f} confidence"
        elif inactive_now and not inactive_before:
            reason = "Newly inactive (>14d since last trade)"

        delta = WalletDelta(
            address=addr,
            label=cur.get("label", addr[:10]),
            prev_confidence=prev_conf,
            new_confidence=new_conf,
            delta_confidence=delta_conf,
            prev_badge=prev_badge,
            new_badge=new_badge,
            badge_changed=badge_changed,
            is_new=is_new,
            is_inactive=inactive_now,
            edge_type=cur.get("edge_type", "unknown"),
            n_resolved=int(diag.get("n_resolved") or 0),
            notable_reason=reason,
        )
        all_deltas.append(delta)

        if is_new and new_conf >= 50:
            new_wallets.append(delta)
        if badge_changed:
            if _badge_rank(new_badge) > _badge_rank(prev_badge or ""):
                promoted.append(delta)
            elif _badge_rank(new_badge) < _badge_rank(prev_badge or ""):
                demoted.append(delta)
        else:
            if delta_conf <= -10:
                decaying.append(delta)
            elif delta_conf >= 10:
                rising.append(delta)
        if inactive_now and not inactive_before and not is_new:
            newly_inactive.append(delta)

    # Sort each list
    new_wallets.sort(key=lambda d: d.new_confidence, reverse=True)
    promoted.sort(key=lambda d: d.new_confidence, reverse=True)
    demoted.sort(key=lambda d: -d.new_confidence)
    decaying.sort(key=lambda d: d.delta_confidence)
    rising.sort(key=lambda d: -d.delta_confidence)

    return TrackingReport(
        scan_ts=current.get("scan_ts", "?"),
        prev_scan_ts=previous.get("scan_ts") if previous else None,
        n_current=len(cur_by_addr),
        n_previous=len(prev_by_addr),
        new_wallets=new_wallets,
        promoted=promoted,
        demoted=demoted,
        decaying=decaying,
        rising=rising,
        newly_inactive=newly_inactive,
        all_deltas=all_deltas,
    )


def report_to_markdown(report: TrackingReport) -> str:
    lines = [
        f"# SC-016 Wallet Tracking — Changelog",
        "",
        f"**Current scan:** {report.scan_ts}",
        f"**Previous scan:** {report.prev_scan_ts or 'none (first scan)'}",
        f"**Wallets:** {report.n_current} (was {report.n_previous})",
        "",
    ]

    if not report.prev_scan_ts:
        lines.append("> First scan — no deltas to report. Re-run later to see changes.")
        return "\n".join(lines)

    def table(title: str, deltas: list[WalletDelta], show_delta: bool = True) -> list[str]:
        if not deltas:
            return [f"### {title}", "", "_None_", ""]
        out = [f"### {title} ({len(deltas)})", ""]
        header = "| Label | Address | Edge | Rsl | "
        if show_delta:
            header += "Prev → New | Δ |"
        else:
            header += "Conf |"
        out.append(header)
        sep = "|" + "|".join(["---"] * (header.count("|") - 1)) + "|"
        out.append(sep)
        for d in deltas[:20]:
            if show_delta and d.prev_confidence is not None:
                conf_cell = f"{d.prev_confidence:.0f} → {d.new_confidence:.0f}"
                delta_cell = f"{d.delta_confidence:+.1f}"
                out.append(
                    f"| {d.label} | `{d.address[:10]}…` | {d.edge_type} | {d.n_resolved} | "
                    f"{conf_cell} | {delta_cell} |"
                )
            else:
                out.append(
                    f"| {d.label} | `{d.address[:10]}…` | {d.edge_type} | {d.n_resolved} | "
                    f"{d.new_confidence:.1f} |"
                )
        out.append("")
        return out

    lines.append("## 🆕 New high-confidence wallets")
    lines.append("")
    lines.append("_Wallets seen for the first time with confidence ≥ 50._")
    lines.append("")
    lines.extend(table("New wallets", report.new_wallets, show_delta=False)[1:])

    lines.append("## ⬆️ Promoted (badge upgrade)")
    lines.append("")
    lines.extend(table("Promoted", report.promoted)[1:])

    lines.append("## ⬇️ Demoted (badge downgrade)")
    lines.append("")
    lines.extend(table("Demoted", report.demoted)[1:])

    lines.append("## 📉 Decaying (confidence -10 or worse)")
    lines.append("")
    lines.extend(table("Decaying", report.decaying)[1:])

    lines.append("## 📈 Rising (confidence +10 or better)")
    lines.append("")
    lines.extend(table("Rising", report.rising)[1:])

    lines.append("## 💤 Newly inactive (>14d since last trade)")
    lines.append("")
    lines.extend(table("Inactive", report.newly_inactive, show_delta=False)[1:])

    return "\n".join(lines)
