#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Telegram notifications for Polymarket bot.

Commands:
    python scripts/notify.py --positions       # open positions snapshot
    python scripts/notify.py --daily           # daily PnL report
    python scripts/notify.py --test            # send a test message
    python scripts/notify.py --msg "text"      # send custom message

Auto-alerts (called by the bot loop):
    from scripts.notify import alert_fill, alert_daily
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

# ── Load .env ─────────────────────────────────────────────────────────────────
_env = Path(__file__).parent.parent / ".env"
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            k, _, v = _line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

# Thresholds for big win / big loss alerts
BIG_WIN_USD  = 1.0   # notify when a single fill profits >= $1
BIG_LOSS_USD = 0.50  # notify when a single fill loses >= $0.50


# ── Core sender ───────────────────────────────────────────────────────────────

def send(text: str) -> bool:
    """Send a Telegram message. Returns True on success."""
    if not BOT_TOKEN or BOT_TOKEN.startswith("replace"):
        print("[Telegram] Token not configured.")
        return False
    import urllib.request, urllib.parse
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
    except Exception as e:
        print(f"[Telegram] Error: {e}")
        return False


# ── Alert templates ───────────────────────────────────────────────────────────

def alert_test() -> bool:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    return send(
        f"<b>Polybot OK</b>\n"
        f"Bot connecte et operationnel\n"
        f"Heure: {now}\n"
        f"Wallet: {os.environ.get('POLYMARKET_FUNDER_ADDRESS','?')[:10]}..."
    )


def alert_fill(
    *,
    market: str,
    side: str,          # BUY / SELL
    price: float,
    size: float,
    pnl_usd: float | None = None,
    strategy: str = "",
) -> bool:
    icon = "BUY" if side.upper() == "BUY" else "SELL"
    pnl_str = ""
    if pnl_usd is not None:
        if pnl_usd >= BIG_WIN_USD:
            pnl_str = f"\nPnL: <b>+${pnl_usd:.2f} WIN</b>"
        elif pnl_usd <= -BIG_LOSS_USD:
            pnl_str = f"\nPnL: <b>-${abs(pnl_usd):.2f} LOSS</b>"
        else:
            pnl_str = f"\nPnL: ${pnl_usd:+.2f}"
    strat_str = f"\nStrategie: {strategy}" if strategy else ""
    return send(
        f"<b>[FILL] {icon}</b>\n"
        f"Marche: {market[:50]}\n"
        f"Prix: {price:.3f} | Size: {size:.1f} shares"
        f"{pnl_str}{strat_str}"
    )


def alert_big_win(*, market: str, pnl_usd: float, strategy: str = "") -> bool:
    return send(
        f"<b>WIN +${pnl_usd:.2f}</b>\n"
        f"{market[:60]}\n"
        f"{('Strategie: ' + strategy) if strategy else ''}"
    )


def alert_big_loss(*, market: str, loss_usd: float, strategy: str = "") -> bool:
    return send(
        f"<b>LOSS -${loss_usd:.2f}</b>\n"
        f"{market[:60]}\n"
        f"{('Strategie: ' + strategy) if strategy else ''}\n"
        f"Verifier les positions ouvertes."
    )


def alert_kill_switch(reason: str) -> bool:
    return send(
        f"<b>KILL SWITCH ACTIVE</b>\n"
        f"Raison: {reason}\n"
        f"Tous les ordres annules. Intervention manuelle requise."
    )


async def _fetch_positions() -> list[dict]:
    """Fetch open positions from Polymarket API."""
    try:
        from polybot.polymarket.api import PolymarketClient
        from polybot.core.config import get_settings
        settings = get_settings()
        wallet = os.environ.get("POLYMARKET_FUNDER_ADDRESS", "")
        async with PolymarketClient(settings) as client:
            positions = await client.get_positions(wallet)
            return positions or []
    except Exception as e:
        print(f"[positions] Error: {e}")
        return []


def alert_positions() -> bool:
    """Send open positions snapshot to Telegram."""
    positions = asyncio.run(_fetch_positions())

    if not positions:
        return send(
            "<b>Positions ouvertes</b>\n"
            "Aucune position ouverte actuellement."
        )

    lines = ["<b>Positions ouvertes</b>"]
    total_value = 0.0

    for p in positions[:15]:  # max 15 pour eviter message trop long
        try:
            question = str(p.get("title") or p.get("market") or "?")[:40]
            outcome  = str(p.get("outcome") or "?")
            size     = float(p.get("size") or p.get("currentValue") or 0)
            avg_price = float(p.get("avgPrice") or p.get("price") or 0)
            cur_price = float(p.get("curPrice") or avg_price)
            value    = size * cur_price
            pnl      = size * (cur_price - avg_price)
            total_value += value
            pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
            lines.append(
                f"\n{question}\n"
                f"  {outcome} | {size:.0f} shares @ {avg_price:.3f}\n"
                f"  Valeur: ${value:.2f} | PnL: {pnl_str}"
            )
        except Exception:
            continue

    lines.append(f"\n<b>Total: ${total_value:.2f}</b>")
    return send("\n".join(lines))


def alert_daily() -> bool:
    """Send daily summary report."""
    today = date.today().isoformat()

    # Load signals from tmp files
    signals_summary = []
    for f in ["tmp/smart_follower_signals.json", "tmp/yes_no_arb_signals.json"]:
        p = Path(f)
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                n = data.get("signals_found") or len(data.get("signals", []))
                signals_summary.append(f"{Path(f).stem}: {n} signaux")
            except Exception:
                pass

    signals_str = "\n".join(signals_summary) if signals_summary else "Aucun scan recemment"

    # Balance check
    balance_str = ""
    try:
        from polybot.wallet.signer import LiveSigner
        signer = LiveSigner.from_env()
        bal = signer.get_balance()
        balance_str = f"\nBalance CLOB: ${bal['balance_usdc']:.2f}"
    except Exception:
        pass

    return send(
        f"<b>Bilan quotidien — {today}</b>\n"
        f"\nScans du jour:\n{signals_str}"
        f"{balance_str}\n"
        f"\nBot actif | LIVE_TRADING: {os.environ.get('LIVE_TRADING_ENABLED','false')}\n"
        f"Bankroll: ${os.environ.get('POLYBOT_BANKROLL_USD','?')}"
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Polybot Telegram notifications")
    parser.add_argument("--test",      action="store_true", help="Send test message")
    parser.add_argument("--positions", action="store_true", help="Send open positions")
    parser.add_argument("--daily",     action="store_true", help="Send daily report")
    parser.add_argument("--msg",       type=str,            help="Send custom message")
    args = parser.parse_args()

    if args.test:
        ok = alert_test()
        print("Sent OK" if ok else "Failed")
    elif args.positions:
        ok = alert_positions()
        print("Sent OK" if ok else "Failed")
    elif args.daily:
        ok = alert_daily()
        print("Sent OK" if ok else "Failed")
    elif args.msg:
        ok = send(args.msg)
        print("Sent OK" if ok else "Failed")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
