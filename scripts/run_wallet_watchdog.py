#!/usr/bin/env python
"""
Wallet Watchdog — SC-016 detection loop 24/7.

Runs a full wallet confidence scan every N hours (default 2h).
Detects two categories and alerts via Telegram:

  QUALIFIED  conf >= min_confidence (default 55)
             → ready to copy via PolyCop

  EMERGING   edge_proof >= edge_threshold (default 65) AND n_resolved <= max_trades (default 20)
             → promising signal but not enough data yet — WATCH ONLY
             → re-evaluated each cycle; promoted alert if it reaches qualified later

Usage:
    PYTHONPATH=src python scripts/run_wallet_watchdog.py
    PYTHONPATH=src python scripts/run_wallet_watchdog.py --once   # single run, then exit
    PYTHONPATH=src python scripts/run_wallet_watchdog.py --interval 3600  # 1h instead of 2h

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GOOGLE CLOUD DEPLOYMENT (e2-micro free tier, ~$0/mois)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Créer la VM (free tier eligible : us-central1, us-east1, us-west1)
   gcloud compute instances create polybot-watchdog \\
       --machine-type=e2-micro \\
       --zone=us-central1-a \\
       --image-family=debian-12 \\
       --image-project=debian-cloud \\
       --boot-disk-size=20GB

2. SSH dans la VM
   gcloud compute ssh polybot-watchdog --zone=us-central1-a

3. Setup (à faire une seule fois dans la VM)
   sudo apt update && sudo apt install python3-pip python3-venv git -y
   git clone https://github.com/TON_COMPTE/polymarket-bot
   cd polymarket-bot
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dashboard,automation]"
   cp .env.example .env && nano .env
   # Ajouter dans .env :
   #   TELEGRAM_BOT_TOKEN=...
   #   TELEGRAM_CHAT_ID=...
   #   TELEGRAM_API_ID=...      (my.telegram.org)
   #   TELEGRAM_API_HASH=...
   #   POLYCOP_WALLET_ADDRESS=...

4. Test (une seule passe)
   PYTHONPATH=src python scripts/run_wallet_watchdog.py --once

5. Démarrer en service systemd (tourne en permanence, redémarre auto)
   sudo tee /etc/systemd/system/polybot-watchdog.service > /dev/null << 'EOF'
   [Unit]
   Description=Polybot Wallet Watchdog
   After=network.target

   [Service]
   Type=simple
   User=YOUR_USERNAME
   WorkingDirectory=/home/YOUR_USERNAME/polymarket-bot
   EnvironmentFile=/home/YOUR_USERNAME/polymarket-bot/.env
   Environment=PYTHONPATH=/home/YOUR_USERNAME/polymarket-bot/src
   ExecStart=/home/YOUR_USERNAME/polymarket-bot/.venv/bin/python scripts/run_wallet_watchdog.py
   Restart=always
   RestartSec=60
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   EOF

   sudo systemctl daemon-reload
   sudo systemctl enable polybot-watchdog
   sudo systemctl start polybot-watchdog

6. Vérifier les logs
   sudo journalctl -u polybot-watchdog -f
   tail -f tmp/watchdog.log

7. Mettre à jour le code sans interrompre le watchdog
   git pull && sudo systemctl restart polybot-watchdog
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

import argparse
import html as _html
import json
import logging
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone as _tz
UTC = _tz.utc
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

# Load .env
_env = ROOT / ".env"
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            k, _, v = _line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

CONF_OUT = ROOT / "tmp" / "wallet_confidence.json"
SNAPS_DIR = ROOT / "tmp" / "wallet_scans"
SEEN_FILE = ROOT / "tmp" / "watchdog_seen.json"
LOG_FILE = ROOT / "tmp" / "watchdog.log"
POLYCOP_QUEUE = ROOT / "tmp" / "polycop_queue.json"

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def _setup_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    try:
        handlers.append(logging.FileHandler(LOG_FILE, encoding="utf-8"))
    except Exception:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [WATCHDOG] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


log = logging.getLogger(__name__)


# ── Telegram ───────────────────────────────────────────────────────────────────

def _tg_send(text: str) -> bool:
    if not BOT_TOKEN or BOT_TOKEN.startswith("replace"):
        log.info(f"[TG not configured] {text[:80]}")
        return False
    payload = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception as exc:
        log.warning(f"Telegram error: {exc}")
        return False


def _alert_qualified(ws: dict) -> None:
    label = ws.get("label") or ws.get("address", "?")[:12]
    addr = ws.get("address", "?")
    conf = ws.get("confidence", 0)
    badge = ws.get("risk_badge", "")
    edge = ws.get("edge_type", "").replace("category_specialist:", "")
    diag = ws.get("diagnostics", {})
    subs = ws.get("sub_scores", {})
    n_res = diag.get("n_resolved", 0)
    pnl = float(diag.get("total_pnl_usd") or 0)
    age = diag.get("last_trade_age_days", 0)
    persist = subs.get("persistence", 0)
    copyability = subs.get("copyability", 0)
    win_rate_lb = float(diag.get("win_rate_wilson_lb") or 0)

    max_pct = 2.0 if "GREEN" in badge else 1.0 if conf >= 60 else 0.5
    min_hold = "5min" if copyability >= 70 else "10min" if copyability >= 55 else "20min"
    stop_conf = max(40, conf - 15)

    # Adresse complète dans un bloc code (tap = copier sur mobile)
    text = (
        f"<b>⭐ NOUVEAU WALLET — COPIER VIA POLYCOP</b>\n\n"
        f"<b>{label}</b>  {badge}\n"
        f"Conf: <b>{conf}/100</b>  |  Edge: {edge}\n"
        f"WR LB: {win_rate_lb:.0%}  |  {n_res} trades  |  PnL: ${pnl:+,.0f}\n"
        f"Actif il y a: {age}j  |  Persist: {persist:.0f}/100\n\n"
        f"📋 <b>Adresse (tap pour copier) :</b>\n"
        f"<code>{addr}</code>\n\n"
        f"<b>Règles PolyCop :</b>\n"
        f"• Taille max : {max_pct:.1f}% du bankroll\n"
        f"• Attends &gt;{min_hold} après l'entrée whale\n"
        f"• Skip si prix &gt;92% (near resolution)\n"
        f"• Stop-follow : conf&lt;{stop_conf} | inactive&gt;14j\n\n"
        f"<i>➡️ PolyCop : Copy Trade → colle l'adresse ci-dessus</i>"
    )
    _tg_send(text)


def _alert_scout(ws: dict, fixed_usd: float) -> None:
    label = ws.get("label") or ws.get("address", "?")[:12]
    addr = ws.get("address", "?")
    conf = ws.get("confidence", 0)
    badge = ws.get("risk_badge", "")
    subs = ws.get("sub_scores", {})
    diag = ws.get("diagnostics", {})
    edge = ws.get("edge_type", "?").replace("category_specialist:", "")
    n_res = diag.get("n_resolved", 0)
    edge_proof = subs.get("edge_proof", 0)
    win_rate = diag.get("win_rate", 0)
    _tg_send(
        f"<b>🔭 SCOUT — auto-copy ${fixed_usd:.2f}/trade</b>\n\n"
        f"<b>{_html.escape(label)}</b>  {badge}\n"
        f"Confiance : {conf} | Edge proof : {edge_proof:.0f}\n"
        f"Win rate : {win_rate:.0%} sur {n_res} trades\n"
        f"Edge type : {edge}\n\n"
        f"<code>{addr}</code>\n\n"
        f"<i>⚠️ Wallet court-terme ({n_res} trades). Taille fixe ${fixed_usd:.2f}/trade.</i>"
    )


def _alert_emerging(ws: dict) -> None:
    label = ws.get("label") or ws.get("address", "?")[:12]
    addr = ws.get("address", "?")
    conf = ws.get("confidence", 0)
    edge = ws.get("edge_type", "").replace("category_specialist:", "")
    diag = ws.get("diagnostics", {})
    subs = ws.get("sub_scores", {})
    n_res = diag.get("n_resolved", 0)
    edge_proof = subs.get("edge_proof", 0)
    win_rate = diag.get("win_rate_wilson_lb", 0) or 0

    text = (
        f"<b>⚡ EMERGING WALLET — WATCH ONLY</b>\n\n"
        f"<b>{label}</b>\n"
        f"<code>{addr[:22]}…</code>\n\n"
        f"Edge proof: <b>{edge_proof:.0f}/100</b> (fort pour {n_res} trades!)\n"
        f"Confiance: {conf} (données insuffisantes)\n"
        f"Edge type: {edge}\n"
        f"WR Wilson LB: {win_rate:.1%}\n\n"
        f"⚠️ NE PAS COPIER — trop peu de data.\n"
        f"Re-évalué chaque scan. Alerte quand conf ≥ 55."
    )
    _tg_send(text)


def _alert_promoted(ws: dict) -> None:
    label = ws.get("label") or ws.get("address", "?")[:12]
    conf = ws.get("confidence", 0)
    badge = ws.get("risk_badge", "")
    text = (
        f"<b>📈 EMERGING → QUALIFIED</b>\n\n"
        f"<b>{label}</b> a atteint conf={conf} {badge}\n"
        f"Était en surveillance depuis quelques scans.\n\n"
        f"➡️ Prêt à copier via PolyCop"
    )
    _tg_send(text)


def _alert_summary(n_qualified: int, n_emerging: int, n_promoted: int, n_total: int, elapsed: float) -> None:
    now = datetime.now(UTC).strftime("%d/%m %H:%M UTC")
    parts = [f"<b>Watchdog — {now}</b>", f"{n_total} wallets scannés | {elapsed:.0f}s"]
    if n_qualified:
        parts.append(f"⭐ {n_qualified} nouveau(x) qualifié(s)")
    if n_promoted:
        parts.append(f"📈 {n_promoted} promu(s) emerging→qualified")
    if n_emerging:
        parts.append(f"⚡ {n_emerging} émergent(s) détecté(s)")
    if not any([n_qualified, n_emerging, n_promoted]):
        parts.append("Aucun nouveau wallet détecté")
    _tg_send("\n".join(parts))


# ── State persistence ──────────────────────────────────────────────────────────

def _load_seen() -> dict[str, str]:
    """Returns {address: 'qualified'|'emerging'}."""
    if not SEEN_FILE.exists():
        return {}
    try:
        data = json.loads(SEEN_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        # Legacy format (just a list)
        return {addr: "qualified" for addr in data}
    except Exception:
        return {}


def _save_seen(seen: dict[str, str]) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(seen, indent=2), encoding="utf-8")


# ── Thread ingester subprocess ─────────────────────────────────────────────────

def _run_thread_ingester() -> None:
    """Process any new .txt files in twitter-threads/inbox/ before each scan."""
    inbox = ROOT / "resources" / "twitter-threads" / "inbox"
    if not inbox.exists() or not any(inbox.glob("*.txt")) and not any(inbox.glob("*.md")):
        return
    cmd = [sys.executable, str(SCRIPTS / "ingest_threads.py")]
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
        if proc.stdout.strip():
            for line in proc.stdout.strip().splitlines():
                log.info(f"[ingest] {line}")
        if proc.returncode != 0 and proc.stderr.strip():
            log.warning(f"Thread ingester error: {proc.stderr.strip()[:200]}")
    except Exception as exc:
        log.warning(f"Thread ingester failed: {exc}")


# ── Scan subprocess ────────────────────────────────────────────────────────────

def _run_scan(args: argparse.Namespace) -> dict | None:
    cmd = [
        sys.executable,
        str(SCRIPTS / "scan_wallet_confidence.py"),
        "--top", str(args.top),
        "--discover-markets", str(args.discover_markets),
        "--activity-limit", str(args.activity_limit),
        "--min-confidence", "30",  # low: we handle qualified/emerging filtering here
    ]
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    log.info(f"Starting scan (top={args.top} lb, {args.discover_markets} markets)…")

    try:
        proc = subprocess.run(
            cmd, env=env, capture_output=True, text=True, timeout=900,
        )
    except subprocess.TimeoutExpired:
        log.error("Scan timed out after 15min")
        return None
    except Exception as exc:
        log.error(f"Scan subprocess error: {exc}")
        return None

    if proc.returncode != 0:
        log.error(f"Scan exited {proc.returncode}: {proc.stderr[:400]}")
        return None

    if not CONF_OUT.exists():
        log.error("No output file after scan")
        return None

    try:
        data = json.loads(CONF_OUT.read_text(encoding="utf-8"))
        n = len(data.get("scores", []))
        log.info(f"Scan complete — {n} wallets scored")
        return data
    except Exception as exc:
        log.error(f"Could not parse scan JSON: {exc}")
        return None


# ── Classification ─────────────────────────────────────────────────────────────

def _classify(
    ws: dict,
    *,
    min_confidence: int,
    edge_threshold: int,
    max_trades: int,
    scout_edge_threshold: int = 72,
    scout_min_conf: int = 42,
    scout_max_trades: int = 20,
) -> str | None:
    """Returns 'qualified', 'scout', 'emerging', or None (skip)."""
    badge = ws.get("risk_badge", "")
    if "BLACK" in badge:
        return None
    if ws.get("diagnostics", {}).get("insider_flag_count", 0) > 0:
        return None

    conf = ws.get("confidence", 0)
    if conf >= min_confidence:
        return "qualified"

    edge_proof = ws.get("sub_scores", {}).get("edge_proof", 0)
    n_resolved = ws.get("diagnostics", {}).get("n_resolved", 9999)

    # SCOUT: strong short-term signal, 5-20 resolved trades, copy at flat $1-2
    if (edge_proof >= scout_edge_threshold
            and scout_min_conf <= conf < min_confidence
            and 5 <= n_resolved <= scout_max_trades):
        return "scout"

    # EMERGING: watch-only, not enough data yet
    if edge_proof >= edge_threshold and n_resolved <= max_trades and conf >= 30:
        return "emerging"

    return None


def _is_scout_for_autocopy(ws: dict, fixed_usd: float = 1.5) -> tuple[bool, str]:
    """
    Lightweight gate for short-term wallets: copy at flat $fixed_usd.

    Bypasses persistence/PnL/category requirements — not enough history to measure them.
    Only requires a strong per-trade edge signal and recent activity.
    """
    badge = ws.get("risk_badge", "")
    diag = ws.get("diagnostics", {})
    subs = ws.get("sub_scores", {})

    if "BLACK" in badge:
        return False, "badge=BLACK (absolute veto)"
    if diag.get("insider_flag_count", 0) > 0:
        return False, "insider_flag detected"

    conf = ws.get("confidence", 0)
    if conf < 42:
        return False, f"conf={conf} < 42 (scout threshold)"

    n_res = diag.get("n_resolved", 0)
    if n_res < 5:
        return False, f"n_resolved={n_res} < 5 (trop peu)"
    if n_res > 20:
        return False, f"n_resolved={n_res} > 20 (utiliser autocopy standard)"

    edge_proof = subs.get("edge_proof", 0)
    if edge_proof < 72:
        return False, f"edge_proof={edge_proof:.0f} < 72 (signal trop faible)"

    age = diag.get("last_trade_age_days", 999)
    if age > 7:
        return False, f"last_trade_age={age}d > 7d (inactif)"

    return True, f"scout OK — n_res={n_res}, edge={edge_proof:.0f}, conf={conf}"


def _is_safe_for_autocopy(ws: dict, autocopy_min_confidence: int = 70) -> tuple[bool, str]:
    """
    Hard filters before queuing a wallet for PolyCop auto-copy.

    Returns (ok, reason). Two tiers:
      GREEN  : conf >= autocopy_min_confidence (default 70), strict filters → 2% sizing
      YELLOW : conf >= 55, relaxed filters → 1% sizing (learning tier)

    All conditions within a tier must pass.
    """
    badge = ws.get("risk_badge", "")
    conf = ws.get("confidence", 0)
    diag = ws.get("diagnostics", {})
    subs = ws.get("sub_scores", {})

    is_green = "GREEN" in badge
    is_yellow = "YELLOW" in badge and not is_green

    # 1. Badge check: must be GREEN or YELLOW
    if not is_green and not is_yellow:
        return False, f"badge={badge.split()[0] if badge else '?'} (need GREEN or YELLOW)"

    # 2. Confidence thresholds
    if is_green and conf < autocopy_min_confidence:
        return False, f"conf={conf} < {autocopy_min_confidence} (GREEN threshold)"
    if is_yellow and conf < 55:
        return False, f"conf={conf} < 55 (YELLOW threshold)"

    # 3. Insider pattern — absolute veto regardless of tier
    if diag.get("insider_flag_count", 0) > 0:
        return False, "insider_flag detected"

    # 4. Sample size (GREEN: 25 trades, YELLOW: 15 trades)
    n_res = diag.get("n_resolved", 0)
    min_trades = 25 if is_green else 15
    if n_res < min_trades:
        return False, f"n_resolved={n_res} < {min_trades} (too few trades)"

    # 5. Recently active — dormant wallets are stale signals
    age = diag.get("last_trade_age_days", 999)
    if age > 14:
        return False, f"last_trade_age={age}d > 14d (dormant)"

    # 6. Anti-luck sub-score (GREEN: 50, YELLOW: 30)
    anti_luck = subs.get("anti_luck", 0)
    min_luck = 50 if is_green else 30
    if anti_luck < min_luck:
        return False, f"anti_luck={anti_luck:.0f} < {min_luck} (luck pattern)"

    # 7. Persistence — edge must hold across time periods (GREEN: 50, YELLOW: 25)
    # YELLOW floor lowered: with 400+ resolved trades the sample compensates for
    # split-half variability — a 71% WR over 491 trades is not a persistence problem.
    persist = subs.get("persistence", 0)
    min_persist = 50 if is_green else 25
    if persist < min_persist:
        return False, f"persistence={persist:.0f} < {min_persist} (unstable edge)"

    # 8. Meaningful PnL (GREEN: $500, YELLOW: $200)
    pnl = float(diag.get("total_pnl_usd") or 0)
    min_pnl = 500 if is_green else 200
    if pnl < min_pnl:
        return False, f"total_pnl=${pnl:.0f} < ${min_pnl} (insufficient track record)"

    # 9. Category concentration — PolyCop copies ALL trades from a wallet.
    # A wallet with 91% WR on crypto but 15% on politics yields net-negative
    # results when copied blindly. Require strong category dominance so that
    # the vast majority of copied trades fall in the wallet's proven edge zone.
    # Threshold: 80% of trades must be in the dominant category.
    # Wallets classified as "general_trader" or "unknown" are blocked entirely.
    edge_type = ws.get("edge_type", "")
    if edge_type in ("general_trader", "unknown", "hft_uncopyable"):
        return False, f"edge_type={edge_type} (no dominant category — copying all trades is net-negative)"
    cat_concentration = diag.get("category_concentration", 0.0)
    min_concentration = 0.80
    if cat_concentration < min_concentration:
        return False, (
            f"category_concentration={cat_concentration:.0%} < {min_concentration:.0%} "
            f"(copy only wallets where ≥80% of trades are in their dominant category)"
        )

    return True, "all checks passed"


def _compute_copy_size_pct(ws: dict) -> float:
    """
    Compute recommended copy size as % of bankroll.

    YELLOW badge → flat 2.5% (~$2.43 on $97 bankroll, raised to min $2.50)
    GREEN badge  → confidence-based formula: 2.0% – 5.0%
    """
    badge = ws.get("risk_badge", "")
    is_green = "GREEN" in badge

    if not is_green:
        # YELLOW: flat 2.5%
        return 2.5

    # GREEN: confidence-based sizing
    conf = ws.get("confidence", 70)
    subs = ws.get("sub_scores", {})

    # Base: 2.0% at conf=70, 5.0% at conf=100 (linear)
    base_pct = 2.0 + (conf - 70) / 30.0 * 3.0
    base_pct = max(2.0, min(5.0, base_pct))

    # Persistence bonus: wallet still edges consistently over time
    persist_bonus = 0.25 if subs.get("persistence", 0) >= 70 else 0.0

    # Anti-luck bonus: diversified PnL, not a lucky jackpot
    luck_bonus = 0.5 if subs.get("anti_luck", 0) >= 70 else 0.0

    return round(min(5.0, base_pct + persist_bonus + luck_bonus), 2)


def _queue_for_polycop(ws: dict) -> None:
    """Add wallet to the PolyCop auto-copy queue."""
    POLYCOP_QUEUE.parent.mkdir(parents=True, exist_ok=True)

    try:
        queue: list[dict] = json.loads(POLYCOP_QUEUE.read_text(encoding="utf-8")) if POLYCOP_QUEUE.exists() else []
    except Exception:
        queue = []

    if any(item.get("address") == ws.get("address") for item in queue):
        return

    diag = ws.get("diagnostics", {})
    size_pct = _compute_copy_size_pct(ws)

    queue.append({
        "address": ws.get("address"),
        "label": ws.get("label") or ws.get("address", "?")[:12],
        "confidence": ws.get("confidence", 0),
        "risk_badge": ws.get("risk_badge", ""),
        "edge_type": ws.get("edge_type", ""),
        "size_pct": size_pct,
        "n_resolved": diag.get("n_resolved", 0),
        "total_pnl_usd": diag.get("total_pnl_usd", 0),
        "queued_at": datetime.now(UTC).isoformat(),
        "status": "pending",
        "tier": "standard",
    })

    POLYCOP_QUEUE.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"Queued for PolyCop auto-copy: {ws.get('label') or ws.get('address','?')[:12]} ({size_pct}% bankroll)")


def _queue_for_polycop_scout(ws: dict, fixed_usd: float) -> None:
    """Add a SCOUT wallet to the queue with a fixed dollar cap (no bankroll %)."""
    POLYCOP_QUEUE.parent.mkdir(parents=True, exist_ok=True)

    try:
        queue: list[dict] = json.loads(POLYCOP_QUEUE.read_text(encoding="utf-8")) if POLYCOP_QUEUE.exists() else []
    except Exception:
        queue = []

    if any(item.get("address") == ws.get("address") for item in queue):
        return

    diag = ws.get("diagnostics", {})
    queue.append({
        "address": ws.get("address"),
        "label": ws.get("label") or ws.get("address", "?")[:12],
        "confidence": ws.get("confidence", 0),
        "risk_badge": ws.get("risk_badge", ""),
        "edge_type": ws.get("edge_type", ""),
        "size_pct": None,
        "fixed_max_per_trade_usd": fixed_usd,
        "n_resolved": diag.get("n_resolved", 0),
        "total_pnl_usd": diag.get("total_pnl_usd", 0),
        "queued_at": datetime.now(UTC).isoformat(),
        "status": "pending",
        "tier": "scout",
    })

    POLYCOP_QUEUE.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"Queued SCOUT for PolyCop: {ws.get('label') or ws.get('address','?')[:12]} (fixed ${fixed_usd})")


# ── Main loop ──────────────────────────────────────────────────────────────────

def run_once(args: argparse.Namespace) -> None:
    _run_thread_ingester()  # ingest new threads before scan
    t0 = time.time()
    data = _run_scan(args)
    if not data:
        log.warning("Scan returned no data — skipping iteration")
        return

    scores: list[dict] = data.get("scores", [])
    seen = _load_seen()

    new_qualified: list[dict] = []
    new_emerging: list[dict] = []
    new_scouts: list[dict] = []
    promoted: list[dict] = []

    for ws in scores:
        addr = ws.get("address", "")
        if not addr:
            continue

        category = _classify(
            ws,
            min_confidence=args.min_confidence,
            edge_threshold=args.edge_threshold,
            max_trades=args.max_emerging_trades,
            scout_edge_threshold=args.scout_edge_threshold,
            scout_min_conf=args.scout_min_conf,
            scout_max_trades=args.scout_max_trades,
        )
        prev_status = seen.get(addr)

        if category == "qualified":
            if prev_status is None:
                new_qualified.append(ws)
                seen[addr] = "qualified"
            elif prev_status in ("emerging", "scout"):
                promoted.append(ws)
                seen[addr] = "qualified"
            # already qualified → no alert

        elif category == "scout":
            if prev_status is None:
                new_scouts.append(ws)
                seen[addr] = "scout"
            # already in seen → no re-alert

        elif category == "emerging":
            if prev_status is None:
                new_emerging.append(ws)
                seen[addr] = "emerging"
            # already in seen → no re-alert

    # Send alerts + queue auto-copy (qualified first, then emerging, then promotions)
    for ws in sorted(new_qualified, key=lambda s: s.get("confidence", 0), reverse=True):
        label = (ws.get("label") or ws.get("address", "?")[:12])
        log.info(f"QUALIFIED  {label:<20}  conf={ws.get('confidence',0)}")
        _alert_qualified(ws)
        time.sleep(1.5)

        # Auto-copy gate: stricter filters before queuing
        ok, reason = _is_safe_for_autocopy(ws, autocopy_min_confidence=args.autocopy_min_confidence)
        if ok:
            _queue_for_polycop(ws)
            size_pct = _compute_copy_size_pct(ws)
            is_green = "GREEN" in ws.get("risk_badge", "")
            tier_label = "🟢 GREEN (conf-based)" if is_green else "🟡 YELLOW (flat 2.5%)"
            _tg_send(
                f"<b>🤖 Auto-copy queued</b>\n"
                f"<b>{label}</b> ajouté à la file PolyCop\n"
                f"Tier : {tier_label}\n"
                f"Taille : <b>{size_pct}%</b> du bankroll\n"
                f"Le bot PolyCop va l'exécuter dans les prochaines secondes."
            )
        else:
            log.info(f"  → skipped auto-copy: {reason}")
            _tg_send(
                f"<b>⚠️ Notification uniquement</b>\n"
                f"<b>{_html.escape(label)}</b> qualifié mais pas auto-copié\n"
                f"Raison: {_html.escape(reason)}"
            )

    for ws in promoted:
        label = (ws.get("label") or ws.get("address", "?")[:12])
        log.info(f"PROMOTED   {label:<20}  conf={ws.get('confidence',0)}")
        _alert_promoted(ws)
        time.sleep(1.5)

        ok, reason = _is_safe_for_autocopy(ws, autocopy_min_confidence=args.autocopy_min_confidence)
        if ok:
            _queue_for_polycop(ws)

    for ws in sorted(new_emerging, key=lambda s: s.get("sub_scores", {}).get("edge_proof", 0), reverse=True):
        ep = ws.get("sub_scores", {}).get("edge_proof", 0)
        n = ws.get("diagnostics", {}).get("n_resolved", 0)
        log.info(f"EMERGING   {(ws.get('label') or ws.get('address','?')[:12]):<20}  edge_proof={ep:.0f}  n_res={n}")
        _alert_emerging(ws)
        time.sleep(1.5)
        # EMERGING → notification only, never auto-copy

    # ── SCOUT: new short-term wallets — copy at flat $fixed_usd ───────────
    for ws in sorted(new_scouts, key=lambda s: s.get("sub_scores", {}).get("edge_proof", 0), reverse=True):
        ep = ws.get("sub_scores", {}).get("edge_proof", 0)
        n = ws.get("diagnostics", {}).get("n_resolved", 0)
        label = ws.get("label") or ws.get("address", "?")[:12]
        log.info(f"SCOUT      {label:<20}  edge_proof={ep:.0f}  n_res={n}  conf={ws.get('confidence', 0)}")

        ok, reason = _is_scout_for_autocopy(ws, fixed_usd=args.scout_fixed_usd)
        if ok:
            _alert_scout(ws, args.scout_fixed_usd)
            _queue_for_polycop_scout(ws, args.scout_fixed_usd)
            seen[ws.get("address", "")] = "scout_queued"
        else:
            # Signal présent mais pas encore copiable — watch only
            _alert_emerging(ws)
            log.info(f"  → scout watch-only: {reason}")
        time.sleep(1.5)

    # ── Re-check autocopy for previously seen "qualified" wallets ──────────
    # Wallets added to seen.json in past scans passed conf≥55 but may have
    # been blocked by stricter autocopy filters (badge RED, anti_luck, etc.).
    # Re-evaluate them every scan so they get queued as soon as they qualify.
    scores_by_addr = {ws.get("address", ""): ws for ws in scores}
    retry_autocopy: list[dict] = []
    retry_scouts: list[dict] = []
    for addr, status in list(seen.items()):
        if status == "qualified" and addr in scores_by_addr:
            ws = scores_by_addr[addr]
            ok, reason = _is_safe_for_autocopy(ws, autocopy_min_confidence=args.autocopy_min_confidence)
            if ok:
                retry_autocopy.append(ws)
                seen[addr] = "autocopy_queued"
        elif status == "scout" and addr in scores_by_addr:
            ws = scores_by_addr[addr]
            ok, reason = _is_scout_for_autocopy(ws, fixed_usd=args.scout_fixed_usd)
            if ok:
                retry_scouts.append(ws)
                seen[addr] = "scout_queued"

    for ws in sorted(retry_autocopy, key=lambda s: s.get("confidence", 0), reverse=True):
        label = ws.get("label") or ws.get("address", "?")[:12]
        log.info(f"RETRY-COPY {label:<20}  conf={ws.get('confidence', 0)}")
        _queue_for_polycop(ws)
        size_pct = _compute_copy_size_pct(ws)
        is_green = "GREEN" in ws.get("risk_badge", "")
        tier_label = "🟢 GREEN (conf-based)" if is_green else "🟡 YELLOW (flat 2.5%)"
        _tg_send(
            f"<b>🔄 Auto-copy (re-check)</b>\n"
            f"<b>{_html.escape(label)}</b> qualifié depuis un scan précédent — passe maintenant les filtres\n"
            f"Tier : {tier_label}\n"
            f"Taille : <b>{size_pct}%</b> du bankroll"
        )
        time.sleep(1.5)

    for ws in sorted(retry_scouts, key=lambda s: s.get("sub_scores", {}).get("edge_proof", 0), reverse=True):
        label = ws.get("label") or ws.get("address", "?")[:12]
        log.info(f"RETRY-SCOUT {label:<20}  conf={ws.get('confidence', 0)}")
        _alert_scout(ws, args.scout_fixed_usd)
        _queue_for_polycop_scout(ws, args.scout_fixed_usd)
        time.sleep(1.5)

    # ── Distribution log — visible chaque scan pour debugger sans SSH ──────
    n_ge70 = sum(1 for ws in scores if ws.get("confidence", 0) >= 70)
    n_ge55 = sum(1 for ws in scores if ws.get("confidence", 0) >= 55)
    blocking: dict[str, int] = {}
    for ws in scores:
        addr = ws.get("address", "")
        if ws.get("confidence", 0) >= 55 and seen.get(addr) != "autocopy_queued":
            _, reason = _is_safe_for_autocopy(ws, autocopy_min_confidence=args.autocopy_min_confidence)
            key = reason.split("(")[0].strip().split("=")[0].strip()
            blocking[key] = blocking.get(key, 0) + 1
    top_blockers = " | ".join(f"{r}×{n}" for r, n in sorted(blocking.items(), key=lambda x: -x[1])[:3])
    log.info(
        f"Distribution — conf≥70: {n_ge70} | conf≥55: {n_ge55} | "
        f"top blockers: {top_blockers or 'none'}"
    )

    _save_seen(seen)

    elapsed = time.time() - t0
    log.info(
        f"Done — {len(new_qualified)} qualified | {len(promoted)} promoted | "
        f"{len(new_scouts)} scouts | {len(new_emerging)} emerging | "
        f"{len(retry_autocopy)} retry-copied | {len(retry_scouts)} retry-scouts | "
        f"{len(scores)} total | {elapsed:.0f}s"
    )

    something_found = bool(new_qualified or new_emerging or promoted or new_scouts or retry_scouts)
    if something_found or args.always_summary:
        _alert_summary(len(new_qualified), len(new_emerging), len(promoted), len(scores), elapsed)


def main() -> None:
    _setup_logging()

    parser = argparse.ArgumentParser(
        description="Wallet Watchdog — 24/7 SC-016 detection loop",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--interval", type=int, default=7200, help="Seconds between scans (7200 = 2h)")
    parser.add_argument("--top", type=int, default=50, help="Leaderboard top N per window (7 windows)")
    parser.add_argument("--discover-markets", type=int, default=60, help="Holders crawl: top N markets")
    parser.add_argument("--activity-limit", type=int, default=500, help="Max activity fetched per wallet")
    parser.add_argument("--min-confidence", type=int, default=55, help="Threshold for QUALIFIED alert")
    parser.add_argument("--edge-threshold", type=int, default=65, help="edge_proof threshold for EMERGING")
    parser.add_argument("--max-emerging-trades", type=int, default=20, help="Max n_resolved for EMERGING")
    parser.add_argument("--autocopy-min-confidence", type=int, default=70, help="Minimum confidence for PolyCop auto-copy (must be GREEN + pass all hard filters)")
    # SCOUT tier: short-term wallets copied at flat dollar amount
    parser.add_argument("--scout-fixed-usd", type=float, default=2.5, help="Fixed $ per trade for SCOUT tier (default $2.50)")
    parser.add_argument("--scout-edge-threshold", type=int, default=72, help="edge_proof min for SCOUT classification")
    parser.add_argument("--scout-min-conf", type=int, default=42, help="Min confidence for SCOUT classification")
    parser.add_argument("--scout-max-trades", type=int, default=20, help="Max n_resolved for SCOUT (short-term wallets only)")
    parser.add_argument("--once", action="store_true", help="Run one scan then exit")
    parser.add_argument("--always-summary", action="store_true", help="Send Telegram summary even when nothing found")
    args = parser.parse_args()

    SNAPS_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "tmp").mkdir(parents=True, exist_ok=True)

    log.info("=" * 60)
    log.info(f"Wallet Watchdog starting")
    log.info(f"  Interval     : {args.interval}s ({args.interval // 3600}h{(args.interval % 3600) // 60:02d}m)")
    log.info(f"  QUALIFIED    : conf >= {args.min_confidence}")
    log.info(f"  EMERGING     : edge_proof >= {args.edge_threshold} AND n_resolved <= {args.max_emerging_trades}")
    log.info(f"  Telegram     : {'configured' if BOT_TOKEN else 'NOT configured (set TELEGRAM_BOT_TOKEN)'}")
    log.info("=" * 60)

    _tg_send(
        f"<b>Watchdog démarré ✅</b>\n"
        f"Scan toutes les {args.interval // 3600}h\n"
        f"QUALIFIED: conf≥{args.min_confidence} | "
        f"EMERGING: edge≥{args.edge_threshold} n≤{args.max_emerging_trades}"
    )

    if args.once:
        run_once(args)
        return

    while True:
        try:
            run_once(args)
        except KeyboardInterrupt:
            log.info("Stopped by user (Ctrl+C)")
            _tg_send("<b>Watchdog arrêté</b> (Ctrl+C)")
            break
        except Exception as exc:
            log.error(f"Unexpected error: {exc}", exc_info=True)
            _tg_send(f"<b>Watchdog erreur</b>\n{str(exc)[:200]}\nRedémarrage dans 5min…")
            time.sleep(300)
            continue

        log.info(f"Next scan in {args.interval}s ({args.interval // 3600}h)…")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
