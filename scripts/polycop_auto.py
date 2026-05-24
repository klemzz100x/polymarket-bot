#!/usr/bin/env python
"""
PolyCop Auto-Copy Bot — Telethon integration.

Lit tmp/polycop_queue.json, exécute chaque wallet via @PolyCop_BOT,
envoie des notifications via ton bot Telegram.
Tourne 24/7 sur la même GCP VM que le watchdog.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SETUP COMPLET (une seule fois, sur la GCP VM via SSH)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Obtenir les credentials Telegram API
   → https://my.telegram.org → "API Development Tools" → Create app
   → Note ton APP_ID (nombre) et APP_HASH (32 chars)

2. Ajouter dans .env :
      TELEGRAM_API_ID=12345678
      TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
      POLYCOP_BOT=@PolyCop_BOT
      POLYCOP_BANKROLL_USD=1000   # ton capital total en $

3. Authentifier (INTERACTIF, une seule fois, sur la VM) :
      python scripts/polycop_auto.py --auth
   → Entrer ton numéro de téléphone (+33...)
   → Entrer le code reçu sur Telegram
   → Crée tmp/polycop.session (garde ce fichier, ne le commit PAS)

4. Découvrir les boutons PolyCop (une seule fois) :
      python scripts/polycop_auto.py --discover
   → Navigate jusqu'à l'écran config et log TOUS les boutons
   → Configure dans .env (les trois premiers sont déjà connus) :
        POLYCOP_MENU_BUTTON=🚀 Copy Trade
        POLYCOP_CREATE_BUTTON=➕️ Create Copy Trade
        POLYCOP_SAVE_BUTTON=<bouton Save/Create en bas de l'écran config>

5. Test avec un faux wallet :
      python scripts/polycop_auto.py --test-wallet 0x000000000000000000000000000000000000dead

6. Démarrer en service :
      sudo systemctl start polybot-polycop

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FLOW POLYCOP (confirmé via UI le 2026-05-24)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /start
    └─ 🚀 Copy Trade
          └─ ➕️ Create Copy Trade
                └─ [écran config avec boutons]
                      ├─ Target Wallet: - ✏️   → click → bot demande adresse → on envoie
                      ├─ Max Per Trade: $-      → click → bot demande montant  → on envoie
                      └─ [Save/Create]          → click → copy trade créé ✅

  Sizing : Max Per Trade = size_pct / 100 × POLYCOP_BANKROLL_USD
  Exemple : bankroll=$1000, conf=82 → size_pct≈1.5% → Max Per Trade=$15

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SERVICE SYSTEMD (/etc/systemd/system/polybot-polycop.service)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Unit]
Description=Polybot PolyCop Auto-Copy
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/polymarket-bot
EnvironmentFile=/home/YOUR_USER/polymarket-bot/.env
Environment=PYTHONPATH=/home/YOUR_USER/polymarket-bot/src
ExecStart=/home/YOUR_USER/polymarket-bot/.venv/bin/python scripts/polycop_auto.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone as _tz
from pathlib import Path

UTC = _tz.utc

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# Load .env
_env = ROOT / ".env"
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            k, _, v = _line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

LOG_FILE = ROOT / "tmp" / "polycop_auto.log"
QUEUE_FILE = ROOT / "tmp" / "polycop_queue.json"
SESSION_FILE = ROOT / "tmp" / "polycop.session"

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

API_ID = int(os.environ.get("TELEGRAM_API_ID", "0") or "0")
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")

POLYCOP_BOT = os.environ.get("POLYCOP_BOT", "@PolyCop_BOT")

# Confirmed via UI 2026-05-24:
POLYCOP_MENU_BUTTON = os.environ.get("POLYCOP_MENU_BUTTON", "🚀 Copy Trade")
POLYCOP_CREATE_BUTTON = os.environ.get("POLYCOP_CREATE_BUTTON", "➕️ Create Copy Trade")
# Unknown — find via --discover (bottom of config screen):
POLYCOP_SAVE_BUTTON = os.environ.get("POLYCOP_SAVE_BUTTON", "")

# User's total capital — runtime value, auto-refreshed from PolyCop every cycle.
# Seed from env on startup; updated in-memory by _refresh_bankroll().
_BANKROLL_USD: float = float(
    os.environ.get("POLYCOP_BANKROLL_USD")
    or os.environ.get("POLYBOT_BANKROLL_USD")
    or "0"
)

POLL_INTERVAL = 30   # seconds between queue checks
CONV_TIMEOUT = 90    # seconds to wait for each PolyCop response
BANKROLL_REFRESH_INTERVAL = 3600  # re-fetch balance from PolyCop every 1h


def _setup_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    try:
        handlers.append(logging.FileHandler(LOG_FILE, encoding="utf-8"))
    except Exception:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [POLYCOP] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


log = logging.getLogger(__name__)


# ── Telegram notifications (own bot) ──────────────────────────────────────────

def _notify(text: str) -> None:
    if not BOT_TOKEN:
        log.info(f"[TG] {text[:80]}")
        return
    payload = urllib.parse.urlencode({
        "chat_id": CHAT_ID, "text": text,
        "parse_mode": "HTML", "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as exc:
        log.warning(f"Notification error: {exc}")


# ── Queue management ───────────────────────────────────────────────────────────

def _load_queue() -> list[dict]:
    if not QUEUE_FILE.exists():
        return []
    try:
        data = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_queue(queue: list[dict]) -> None:
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")


def _get_pending(queue: list[dict]) -> list[dict]:
    return [item for item in queue if item.get("status") == "pending"]


def _mark_done(queue: list[dict], address: str, success: bool, note: str = "") -> None:
    for item in queue:
        if item.get("address") == address:
            item["status"] = "done" if success else "failed"
            item["processed_at"] = datetime.now(UTC).isoformat()
            item["note"] = note
            break


# ── Telethon helpers ───────────────────────────────────────────────────────────

def _check_telethon() -> bool:
    try:
        import telethon  # noqa: F401
        return True
    except ImportError:
        log.error("telethon not installed. Run: pip install telethon")
        return False


def _require_credentials() -> bool:
    if not API_ID or not API_HASH:
        log.error(
            "Missing Telegram API credentials.\n"
            "1. Go to https://my.telegram.org → API Development Tools\n"
            "2. Create an app and add to .env:\n"
            "   TELEGRAM_API_ID=12345678\n"
            "   TELEGRAM_API_HASH=your32charhash"
        )
        return False
    return True


def _get_client():
    from telethon.sync import TelegramClient
    return TelegramClient(str(SESSION_FILE), API_ID, API_HASH)


# ── Live bankroll detection ────────────────────────────────────────────────────

import re as _re

def _parse_balance_from_text(text: str) -> float | None:
    """
    Extract a USD balance from PolyCop's home screen text.
    Handles patterns like: "$35.00", "35.00 USDC", "Balance: $35", "💰 35.00$"
    Returns float or None if nothing found.
    """
    patterns = [
        r'\$\s*([\d,]+(?:\.\d{1,2})?)',       # $35.00 or $1,234.56
        r'([\d,]+(?:\.\d{1,2})?)\s*\$',       # 35.00$
        r'([\d,]+(?:\.\d{1,2})?)\s*USDC',     # 35.00 USDC
        r'[Bb]alance[:\s]+\$?([\d,]+(?:\.\d{1,2})?)',  # Balance: 35
        r'[Pp]ortfolio[:\s]+\$?([\d,]+(?:\.\d{1,2})?)',
    ]
    for pattern in patterns:
        m = _re.search(pattern, text)
        if m:
            try:
                val = float(m.group(1).replace(",", ""))
                if val > 0:
                    return val
            except ValueError:
                continue
    return None


async def _refresh_bankroll(client) -> float:
    """
    Fetch the user's live balance from PolyCop's /start screen.
    Updates _BANKROLL_USD in-module if a valid balance is found.
    Returns the (possibly unchanged) bankroll.
    """
    global _BANKROLL_USD
    try:
        async with client.conversation(POLYCOP_BOT, timeout=30) as conv:
            await conv.send_message("/start")
            msg = await asyncio.wait_for(conv.get_response(), timeout=30)
            text = msg.text or ""
            log.debug(f"PolyCop /start response: {text[:200]}")

            balance = _parse_balance_from_text(text)
            if balance and balance > 0:
                if abs(balance - _BANKROLL_USD) > 0.01:
                    log.info(f"Bankroll updated: ${_BANKROLL_USD:.2f} → ${balance:.2f}")
                    _notify(f"<b>💰 Bankroll mis à jour</b>: <b>${balance:.2f}</b>")
                    _BANKROLL_USD = balance
                else:
                    log.debug(f"Bankroll unchanged: ${_BANKROLL_USD:.2f}")
            else:
                log.debug(f"No balance found in PolyCop response — keeping ${_BANKROLL_USD:.2f}")
    except Exception as exc:
        log.warning(f"Bankroll refresh failed: {exc} — keeping ${_BANKROLL_USD:.2f}")

    return _BANKROLL_USD


# ── Button navigation ──────────────────────────────────────────────────────────

def _find_button(buttons, *label_hints: str):
    """Find a button matching any label_hint (case-insensitive substring). Returns btn or None."""
    if not buttons:
        return None
    for row in buttons:
        for btn in row:
            btn_text = (getattr(btn, "text", "") or "").lower().strip()
            for hint in label_hints:
                if hint.lower().strip() in btn_text:
                    return btn
    return None


def _log_buttons(message, prefix: str = "") -> None:
    """Log all available buttons on a message for debugging."""
    if not getattr(message, "buttons", None):
        log.info(f"{prefix} (no buttons)")
        return
    for i, row in enumerate(message.buttons):
        for j, btn in enumerate(row):
            log.info(f"{prefix} button[{i}][{j}]: '{getattr(btn, 'text', '?')}'")


def _print_buttons(message, prefix: str = "") -> None:
    """Print all buttons (used in discover mode)."""
    if not getattr(message, "buttons", None):
        print(f"{prefix}  (no buttons)")
        return
    for row in message.buttons:
        for btn in row:
            print(f"{prefix}  → '{getattr(btn, 'text', '?')}'")


async def _click_setting(conv, config_msg, btn_hint: str, value: str) -> tuple[object, bool]:
    """
    Click a settings button, wait for the bot's input prompt, send value, wait for
    the updated config message.

    Returns (updated_msg, success).
    After sending the value, PolyCop may:
      a) send a NEW config message (we catch with get_response)
      b) edit the existing config message (we catch with get_edit)
    We try both with short timeouts.
    """
    btn = _find_button(config_msg.buttons, btn_hint)
    if not btn:
        log.warning(f"Setting button '{btn_hint}' not found on config screen")
        _log_buttons(config_msg, "  available:")
        return config_msg, False

    log.info(f"Clicking setting '{btn_hint}' → value '{value}'")
    await btn.click()

    # Bot should send a prompt message asking for the value
    try:
        prompt = await asyncio.wait_for(conv.get_response(), timeout=CONV_TIMEOUT)
        log.info(f"  Prompt received: {(prompt.text or '')[:80]}")
    except asyncio.TimeoutError:
        log.warning(f"  No prompt received for '{btn_hint}' — may be a toggle, skipping")
        return config_msg, False

    # Send our value
    await conv.send_message(value)
    log.info(f"  Sent: '{value}'")

    # Wait for updated config (new message)
    try:
        updated = await asyncio.wait_for(conv.get_response(), timeout=CONV_TIMEOUT)
        log.info(f"  Config updated (new message): {(updated.text or '')[:60]}")
        _log_buttons(updated, "  updated config")
        return updated, True
    except asyncio.TimeoutError:
        pass

    # Fallback: bot edited the original message
    try:
        updated = await asyncio.wait_for(conv.get_edit(), timeout=15)
        log.info(f"  Config updated (edited message): {(updated.text or '')[:60]}")
        return updated, True
    except asyncio.TimeoutError:
        log.warning(f"  No config update received after setting '{btn_hint}' — continuing anyway")
        return config_msg, True  # optimistic: value was probably accepted


# ── Core PolyCop flow ──────────────────────────────────────────────────────────

async def _follow_wallet_polycop(
    client, wallet_addr: str, label: str, size_pct: float
) -> tuple[bool, str]:
    """
    Navigate PolyCop's Telegram UI to create a copy trade for wallet_addr.

    Flow:
      /start → 🚀 Copy Trade → ➕️ Create Copy Trade → config screen
        → Target Wallet (set address)
        → Max Per Trade (set $ amount from size_pct × bankroll)
        → Save/Create

    Returns (success, message).
    """
    # Compute Max Per Trade in dollars from live bankroll
    if _BANKROLL_USD > 0:
        max_per_trade_usd = round(size_pct / 100.0 * _BANKROLL_USD, 2)
        size_label = f"${max_per_trade_usd} (={size_pct:.1f}% × ${_BANKROLL_USD:.2f})"
    else:
        max_per_trade_usd = 0
        size_label = f"{size_pct:.1f}% (bankroll unknown — Max Per Trade skipped)"
        log.warning("Bankroll is 0 — Max Per Trade will not be configured")

    log.info(f"Starting PolyCop flow for {label} ({wallet_addr[:16]}…)  size={size_label}")

    try:
        async with client.conversation(POLYCOP_BOT, timeout=CONV_TIMEOUT) as conv:

            # ── Step 1: main menu ──────────────────────────────────────────────
            await conv.send_message("/start")
            main_menu = await conv.get_response()
            log.info(f"Main menu: {(main_menu.text or '')[:80]}")
            _log_buttons(main_menu, "  main_menu")

            # ── Step 2: Copy Trade section ─────────────────────────────────────
            btn = _find_button(main_menu.buttons, POLYCOP_MENU_BUTTON)
            if not btn:
                _log_buttons(main_menu, "  available:")
                return False, f"'{POLYCOP_MENU_BUTTON}' not found in main menu"

            await btn.click()
            section = await conv.get_response()
            log.info(f"Section: {(section.text or '')[:80]}")
            _log_buttons(section, "  section")

            # ── Step 3: Create Copy Trade ──────────────────────────────────────
            btn = _find_button(section.buttons, POLYCOP_CREATE_BUTTON, "create copy")
            if not btn:
                _log_buttons(section, "  available:")
                return False, f"'{POLYCOP_CREATE_BUTTON}' not found in Copy Trade section"

            await btn.click()
            # PolyCop sends "loading add page..." as a text prompt for the wallet address
            loading_prompt = await conv.get_response()
            log.info(f"  Wallet prompt: {(loading_prompt.text or '')[:80]}")

            # ── Step 4: Send wallet address as text ───────────────────────────
            # PolyCop asks for the address via text prompt (not a button).
            # The "loading add page..." message IS the prompt — reply with the address.
            await conv.send_message(wallet_addr)
            log.info(f"  Sent wallet address: {wallet_addr}")

            # PolyCop responds with the full config screen (address pre-filled)
            config = await asyncio.wait_for(conv.get_response(), timeout=CONV_TIMEOUT)
            log.info(f"  Config after address: {(config.text or '')[:80]}")
            _log_buttons(config, "  config_after_addr")

            # If still no buttons, PolyCop may edit the message
            if not getattr(config, "buttons", None):
                log.info("  No buttons yet — waiting for edit…")
                try:
                    config = await asyncio.wait_for(conv.get_edit(), timeout=CONV_TIMEOUT)
                    _log_buttons(config, "  config_edit")
                except asyncio.TimeoutError:
                    return False, "Config screen never appeared after sending wallet address"

            # ── Step 5: Set Max Per Trade ──────────────────────────────────────
            if max_per_trade_usd > 0:
                config, ok = await _click_setting(
                    conv, config, "Max Per Trade", str(max_per_trade_usd)
                )
                if not ok:
                    log.warning("Max Per Trade setting failed — continuing to save anyway")

            # ── Step 6: Save / Create ──────────────────────────────────────────
            # Save button is "+ Create" (confirmed via UI screenshot 2026-05-24)
            save_hints = list(filter(None, [
                POLYCOP_SAVE_BUTTON, "+ create", "create", "✅ create",
                "save", "✅ save", "confirm", "done", "submit", "✅",
            ]))
            save_btn = _find_button(config.buttons, *save_hints)

            if not save_btn:
                log.warning("Save button not found — logging all available buttons")
                _log_buttons(config, "  [SAVE NEEDED]")
                return False, (
                    "Save button not found. Run --discover to find its label, "
                    "then set POLYCOP_SAVE_BUTTON in .env"
                )

            log.info(f"Clicking save: '{getattr(save_btn, 'text', '?')}'")
            await save_btn.click()

            try:
                final = await asyncio.wait_for(conv.get_response(), timeout=CONV_TIMEOUT)
                result_text = (final.text or "copy trade created")[:200]
            except asyncio.TimeoutError:
                # Some bots don't send a confirmation after save
                result_text = "no confirmation message — likely created OK"

            log.info(f"  Final: {result_text}")
            return True, result_text

    except asyncio.TimeoutError:
        return False, f"timeout waiting for PolyCop response (>{CONV_TIMEOUT}s)"
    except Exception as exc:
        log.error(f"PolyCop flow error: {exc}", exc_info=True)
        return False, f"error: {exc}"


# ── Commands ───────────────────────────────────────────────────────────────────

def cmd_auth() -> None:
    """Interactive authentication — run once on the GCP VM."""
    if not _check_telethon() or not _require_credentials():
        return

    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    client = _get_client()

    log.info(f"Starting interactive auth. Session will be saved to: {SESSION_FILE}")
    log.info("You'll be asked for your phone number (+33...) and Telegram verification code.")

    with client:
        me = client.get_me()
        log.info(f"Authenticated as: {me.first_name} (@{me.username})")
        print(f"\n✅ Auth successful: {me.first_name} (@{me.username})")
        print(f"   Session saved to: {SESSION_FILE}")
        print("   Keep this file safe — it gives full access to your Telegram account.")


def cmd_discover() -> None:
    """Navigate to PolyCop's config screen and log ALL buttons — used to find POLYCOP_SAVE_BUTTON."""
    if not _check_telethon() or not _require_credentials():
        return
    if not SESSION_FILE.exists():
        log.error(f"Session file not found: {SESSION_FILE}\nRun: python scripts/polycop_auto.py --auth")
        return

    async def _discover():
        client = _get_client()
        async with client:
            print("\n" + "="*60)
            print("POLYCOP BUTTON DISCOVERY")
            print("="*60)

            async with client.conversation(POLYCOP_BOT, timeout=60) as conv:

                # Step 1 — main menu
                await conv.send_message("/start")
                main_menu = await conv.get_response()
                print(f"\n[MAIN MENU] {(main_menu.text or '')[:120]}")
                _print_buttons(main_menu, "[MAIN MENU]")

                # Step 2 — Copy Trade section
                btn = _find_button(main_menu.buttons, POLYCOP_MENU_BUTTON)
                if not btn:
                    print(f"\n⚠️  Button '{POLYCOP_MENU_BUTTON}' not found in main menu")
                    return
                await btn.click()
                section = await conv.get_response()
                print(f"\n[COPY TRADE SECTION] {(section.text or '')[:120]}")
                _print_buttons(section, "[COPY TRADE SECTION]")

                # Step 3 — Create Copy Trade → config screen
                btn = _find_button(section.buttons, POLYCOP_CREATE_BUTTON, "create copy")
                if not btn:
                    print(f"\n⚠️  Button '{POLYCOP_CREATE_BUTTON}' not found in section")
                    return
                await btn.click()
                config = await conv.get_response()
                print(f"\n[CONFIG SCREEN] {(config.text or '')[:120]}")
                print("[CONFIG SCREEN] All buttons:")
                _print_buttons(config, "[CONFIG SCREEN]")

            print("\n" + "="*60)
            print("Next step:")
            print("  Look for the Save/Create/Confirm button in [CONFIG SCREEN] above.")
            print("  Then add to .env:")
            print("    POLYCOP_SAVE_BUTTON=<exact button label>")
            print("    POLYCOP_BANKROLL_USD=<your total capital in $>")
            print("="*60 + "\n")

    asyncio.run(_discover())


def cmd_test_wallet(wallet_addr: str) -> None:
    """Test the full PolyCop flow with a real (or dummy) address."""
    if not _check_telethon() or not _require_credentials():
        return
    if not SESSION_FILE.exists():
        log.error("Not authenticated. Run: python scripts/polycop_auto.py --auth")
        return

    print(f"\nTesting PolyCop flow for wallet: {wallet_addr}")
    print(f"  Bankroll (seed from env): ${_BANKROLL_USD:.2f}")
    print(f"  size_pct: 1.0%  →  Max Per Trade: ${_BANKROLL_USD * 0.01:.2f}")
    print(f"  POLYCOP_SAVE_BUTTON: '{POLYCOP_SAVE_BUTTON or '(not set — will try common patterns)'}'")

    async def _test():
        client = _get_client()
        async with client:
            ok, msg = await _follow_wallet_polycop(client, wallet_addr, "test", 1.0)
            status = "✅ SUCCESS" if ok else "❌ FAILED"
            print(f"\n{status}: {msg}")

    asyncio.run(_test())


# ── Main loop ──────────────────────────────────────────────────────────────────

async def _process_queue_once(client) -> int:
    """Process all pending items in the queue. Returns number processed."""
    queue = _load_queue()
    pending = _get_pending(queue)

    if not pending:
        return 0

    log.info(f"Processing {len(pending)} pending item(s) from queue")
    processed = 0

    for item in pending:
        addr = item.get("address", "?")
        label = item.get("label", addr[:12])
        conf = item.get("confidence", 0)
        size_pct = item.get("size_pct", 1.0)
        badge = item.get("risk_badge", "")
        edge = item.get("edge_type", "").replace("category_specialist:", "")
        max_per_trade = round(size_pct / 100.0 * _BANKROLL_USD, 2) if _BANKROLL_USD > 0 else 0

        log.info(f"Processing: {label} ({addr[:16]}…) conf={conf} size={size_pct}% max_trade=${max_per_trade}")

        ok, result_msg = await _follow_wallet_polycop(client, addr, label, size_pct)

        if ok:
            log.info(f"  ✅ {label}: {result_msg[:80]}")
            _notify(
                f"<b>✅ PolyCop copy trade créé</b>\n\n"
                f"<b>{label}</b>  {badge}\n"
                f"Confiance : {conf} | Edge : {edge}\n"
                f"Taille : <b>${max_per_trade}</b> max/trade "
                f"(<b>{size_pct}%</b> × ${_BANKROLL_USD:.0f})\n\n"
                f"<code>{addr}</code>\n\n"
                f"PolyCop va maintenant copier ce wallet automatiquement."
            )
        else:
            log.warning(f"  ❌ {label}: {result_msg}")
            _notify(
                f"<b>❌ PolyCop auto-copy échoué</b>\n\n"
                f"<b>{label}</b>\n"
                f"Erreur : {result_msg}\n\n"
                f"<code>{addr}</code>\n\n"
                f"Vérifie les logs : <code>tail -f tmp/polycop_auto.log</code>"
            )

        _mark_done(queue, addr, ok, result_msg)
        _save_queue(queue)
        processed += 1

        # Small delay between wallets to avoid PolyCop rate limits
        if processed < len(pending):
            await asyncio.sleep(5)

    return processed


async def _main_loop() -> None:
    if not _check_telethon() or not _require_credentials():
        return
    if not SESSION_FILE.exists():
        log.error(
            f"Session file not found: {SESSION_FILE}\n"
            "Run first: python scripts/polycop_auto.py --auth"
        )
        return

    log.info("="*60)
    log.info("PolyCop Auto-Copy Bot starting")
    log.info(f"  Bot          : {POLYCOP_BOT}")
    log.info(f"  Bankroll seed: ${_BANKROLL_USD:.2f} (will auto-refresh from PolyCop)")
    log.info(f"  Queue file   : {QUEUE_FILE}")
    log.info(f"  Poll interval: {POLL_INTERVAL}s")
    log.info(f"  Menu button  : '{POLYCOP_MENU_BUTTON}'")
    log.info(f"  Create button: '{POLYCOP_CREATE_BUTTON}'")
    log.info(f"  Save button  : '{POLYCOP_SAVE_BUTTON or '(auto-detect)'}'")
    log.info("="*60)

    if not POLYCOP_SAVE_BUTTON:
        log.warning("POLYCOP_SAVE_BUTTON not set — will try common patterns.")

    client = _get_client()
    async with client:

        # Fetch live bankroll from PolyCop immediately at startup
        await _refresh_bankroll(client)
        log.info(f"Live bankroll: ${_BANKROLL_USD:.2f}")

        _notify(
            f"<b>🤖 PolyCop Auto-Copy Bot démarré ✅</b>\n"
            f"Bankroll live : <b>${_BANKROLL_USD:.2f}</b> | Poll : {POLL_INTERVAL}s"
        )

        last_bankroll_refresh = asyncio.get_event_loop().time()

        while True:
            try:
                # Refresh bankroll from PolyCop every hour
                now = asyncio.get_event_loop().time()
                if now - last_bankroll_refresh >= BANKROLL_REFRESH_INTERVAL:
                    await _refresh_bankroll(client)
                    last_bankroll_refresh = now

                n = await _process_queue_once(client)
                if n:
                    log.info(f"Processed {n} wallet(s) from queue")
            except KeyboardInterrupt:
                log.info("Stopped by user")
                _notify("<b>🤖 PolyCop bot arrêté</b>")
                break
            except Exception as exc:
                log.error(f"Error in queue processing: {exc}", exc_info=True)
                _notify(f"<b>❌ PolyCop bot erreur</b>\n{str(exc)[:200]}")
                await asyncio.sleep(60)
                continue

            await asyncio.sleep(POLL_INTERVAL)


def main() -> None:
    _setup_logging()

    parser = argparse.ArgumentParser(
        description="PolyCop Auto-Copy Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--auth", action="store_true", help="Interactive Telegram auth (run once on GCP VM)")
    parser.add_argument("--discover", action="store_true", help="Navigate to config screen and log all buttons")
    parser.add_argument("--test-wallet", type=str, metavar="0xADDR", help="Test full flow with a wallet address")
    args = parser.parse_args()

    if args.auth:
        cmd_auth()
    elif args.discover:
        cmd_discover()
    elif args.test_wallet:
        cmd_test_wallet(args.test_wallet)
    else:
        asyncio.run(_main_loop())


if __name__ == "__main__":
    main()
