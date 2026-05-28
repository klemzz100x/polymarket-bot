#!/usr/bin/env python
"""
Thread Wallet Ingester — SC-016 pipeline.

Lit les fichiers .txt/.md dans resources/twitter-threads/inbox/,
extrait les adresses wallet (0x direct + username → lookup API Polymarket),
déduplique contre resources/thread_wallets.json, déplace les fichiers traités.

Usage:
    PYTHONPATH=src python scripts/ingest_threads.py              # traite l'inbox
    PYTHONPATH=src python scripts/ingest_threads.py --dry-run    # simulation
    PYTHONPATH=src python scripts/ingest_threads.py --stats      # état du store
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import datetime, timezone as _tz
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX_DIR     = ROOT / "resources" / "twitter-threads" / "inbox"
PROCESSED_DIR = ROOT / "resources" / "twitter-threads" / "processed"
STORE_FILE    = ROOT / "resources" / "thread_wallets.json"

UTC = _tz.utc

# ── Regex ──────────────────────────────────────────────────────────────────────

_ADDR_RE = re.compile(r'\b(0x[0-9a-fA-F]{40})\b', re.IGNORECASE)
_MENTION_RE = re.compile(r'@([A-Za-z0-9_]{2,30})')
_PROFILE_URL_RE = re.compile(
    r'polymarket\.com/profile/(0x[0-9a-fA-F]{40}|[A-Za-z0-9_\-]{2,40})',
    re.IGNORECASE,
)
# polymarket.com/@username (most common format in threads)
_AT_PROFILE_URL_RE = re.compile(
    r'polymarket\.com/@([A-Za-z0-9_\-]{2,40})',
    re.IGNORECASE,
)
_TWEET_URL_RE = re.compile(r'https?://(?:twitter\.com|x\.com)/\S+')

# Common non-Polymarket mentions to skip
_SKIP_MENTIONS = {
    "polymarket", "claude", "anthropic", "openai", "gpt", "twitter", "x",
    "everyone", "someone", "anyone", "nobody", "people", "user", "users",
}


# ── Extraction ─────────────────────────────────────────────────────────────────

def extract_addresses(text: str) -> list[str]:
    return list({m.lower() for m in _ADDR_RE.findall(text)})


def extract_usernames(text: str) -> list[str]:
    found: set[str] = set()

    # polymarket.com/@username (highest priority — definitive Polymarket usernames)
    for m in _AT_PROFILE_URL_RE.findall(text):
        found.add(m)

    # polymarket.com/profile/USERNAME
    for m in _PROFILE_URL_RE.findall(text):
        if not _ADDR_RE.match(m):
            found.add(m)

    # @mentions in text (lower priority — may include non-Polymarket accounts)
    for m in _MENTION_RE.findall(text):
        if m.lower() not in _SKIP_MENTIONS and len(m) >= 3:
            found.add(m)

    return list(found)


def extract_source_url(text: str) -> str:
    m = _TWEET_URL_RE.search(text)
    return m.group(0) if m else ""


# ── Polymarket username → wallet lookup ────────────────────────────────────────

async def lookup_username(username: str) -> str | None:
    """Resolve Polymarket username → proxy wallet address."""
    try:
        import httpx
    except ImportError:
        return None

    candidates = [
        f"https://data-api.polymarket.com/profiles?slug={username}",
        f"https://data-api.polymarket.com/profiles?username={username}",
        f"https://data-api.polymarket.com/profiles?name={username}",
        f"https://gamma-api.polymarket.com/users?slug={username}",
        f"https://gamma-api.polymarket.com/users?username={username}",
    ]
    headers = {"User-Agent": "Mozilla/5.0 polybot-ingest/1.0"}

    def _extract(data: object) -> str | None:
        entry = data[0] if isinstance(data, list) and data else data
        if not isinstance(entry, dict):
            return None
        addr = (
            entry.get("proxyWallet") or entry.get("proxy_wallet")
            or entry.get("address") or entry.get("walletAddress")
        )
        return str(addr).lower() if addr and _ADDR_RE.match(str(addr)) else None

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        for url in candidates:
            try:
                r = await client.get(url, headers=headers)
                if r.status_code != 200:
                    continue
                result = _extract(r.json())
                if result:
                    return result
            except Exception:
                continue
    return None


# ── Store helpers ──────────────────────────────────────────────────────────────

def load_store() -> list[dict]:
    if not STORE_FILE.exists():
        return []
    try:
        return json.loads(STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_store(store: list[dict]) -> None:
    STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STORE_FILE.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Core ingestion ─────────────────────────────────────────────────────────────

async def ingest_text(
    text: str,
    *,
    source_name: str = "inline",
    source_url: str = "",
    dry_run: bool = False,
    verbose: bool = True,
) -> list[dict]:
    """Extract + lookup wallets from one thread. Returns newly added entries."""
    store = load_store()
    existing = {e["address"].lower() for e in store}
    now = datetime.now(UTC).strftime("%Y-%m-%d")
    new_entries: list[dict] = []

    def _add(addr: str, label: str, method: str, notes: str = "") -> None:
        addr = addr.lower()
        if addr in existing:
            if verbose:
                print(f"  ⟳  [{method}] {addr[:16]}… déjà présent")
            return
        entry = {
            "address": addr,
            "label": label,
            "source_thread": source_name,
            "source_url": source_url,
            "added_at": now,
            "edge_hint": "unknown",
            "notes": notes,
            "active": True,
            "lookup_method": method,
        }
        new_entries.append(entry)
        existing.add(addr)
        if verbose:
            print(f"  ✅ [{method}] {label} → {addr}")

    # 1. Direct 0x addresses
    for addr in extract_addresses(text):
        _add(addr, addr[:12], "direct_address")

    # 2. Username → API lookup
    usernames = extract_usernames(text)
    if usernames:
        if verbose:
            print(f"  🔍 Lookup {len(usernames)} username(s) : {', '.join(usernames[:8])}")
        results = await asyncio.gather(
            *[lookup_username(u) for u in usernames], return_exceptions=True
        )
        for username, addr in zip(usernames, results):
            if isinstance(addr, Exception) or not addr:
                if verbose:
                    print(f"  ✗  @{username} — non trouvé sur Polymarket")
                continue
            _add(addr, username, "username_lookup", f"résolu depuis @{username}")

    if new_entries and not dry_run:
        store.extend(new_entries)
        save_store(store)

    return new_entries


async def process_inbox(dry_run: bool = False) -> int:
    """Traite tous les fichiers dans inbox/. Retourne le nombre de wallets ajoutés."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(INBOX_DIR.glob("*.txt")) + sorted(INBOX_DIR.glob("*.md"))
    if not files:
        print("📭 Inbox vide — aucun fichier à traiter.")
        return 0

    total = 0
    for f in files:
        print(f"\n📄 {f.name}")
        text = f.read_text(encoding="utf-8", errors="replace")
        source_url = extract_source_url(text)
        new = await ingest_text(
            text, source_name=f.name, source_url=source_url, dry_run=dry_run
        )
        total += len(new)
        if not dry_run:
            ts = datetime.now(UTC).strftime("%H%M%S")
            dest = PROCESSED_DIR / f.name
            if dest.exists():
                dest = PROCESSED_DIR / f"{f.stem}_{ts}{f.suffix}"
            f.rename(dest)
            print(f"  → déplacé vers processed/")

    return total


def print_stats() -> None:
    store = load_store()
    active = [e for e in store if e.get("active", True)]
    sources = {}
    for e in active:
        src = e.get("source_thread", "?")
        sources[src] = sources.get(src, 0) + 1

    print(f"\n{'='*60}")
    print(f"Thread Wallets Store — {STORE_FILE}")
    print(f"{'='*60}")
    print(f"Total : {len(store)} wallets  |  Actifs : {len(active)}")
    print(f"\nPar source :")
    for src, n in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {n:3d}  {src}")
    print(f"{'='*60}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Thread Wallet Ingester")
    parser.add_argument("--dry-run", action="store_true",
                        help="Montre ce qui serait ajouté sans sauvegarder")
    parser.add_argument("--stats", action="store_true",
                        help="Affiche l'état du store et quitte")
    args = parser.parse_args()

    if args.stats:
        print_stats()
        return

    n = asyncio.run(process_inbox(dry_run=args.dry_run))
    store = load_store()
    prefix = "DRY RUN — " if args.dry_run else ""
    print(f"\n{prefix}Ajouté : {n} wallet(s). Store total : {len(store)}.")


if __name__ == "__main__":
    main()
