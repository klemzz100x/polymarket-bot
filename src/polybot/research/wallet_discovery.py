"""SC-016 — Wallet discovery via /holders crawl.

Discovers new wallet seeds by:
  1. Listing top-volume active markets
  2. For each, fetching /holders (returns top holders per outcome token)
  3. Extracting addresses with significant USD exposure
  4. Returning deduped list of candidate seeds for scoring

This is the fast-detect mechanism: high-volume markets attract sharp wallets,
so their top holders are a fertile pool of new candidates beyond what threads name.
"""
from __future__ import annotations

import asyncio
from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _is_valid_address(addr: str) -> bool:
    if not addr or len(addr) != 42 or not addr.startswith("0x"):
        return False
    try:
        int(addr[2:], 16)
        return True
    except ValueError:
        return False


async def discover_from_holders(
    client,
    *,
    n_markets: int = 50,
    holders_per_market: int = 30,
    min_holder_size_usd: float = 200.0,
    market_concurrency: int = 4,
) -> list[dict]:
    """Crawl top markets for new wallet candidates.

    Args:
        client: PolymarketClient instance (already entered).
        n_markets: How many active markets to scan.
        holders_per_market: Top N holders per market to inspect.
        min_holder_size_usd: Min USD-equivalent holding to qualify as a seed.
        market_concurrency: Parallel /holders calls.

    Returns:
        List of seed dicts with address, label, source, hint.
    """
    # Fetch active markets
    try:
        markets = await client.list_markets(active=True, closed=False, limit=n_markets * 3)
    except Exception as e:
        print(f"  ⚠️  list_markets failed: {e}")
        return []

    # Sort by volume desc, keep top n_markets
    def market_volume(m: dict) -> float:
        return _safe_float(m.get("volume") or m.get("volumeNum") or m.get("volume24hr"))

    markets = [m for m in markets if m.get("conditionId")]
    markets.sort(key=market_volume, reverse=True)
    markets = markets[:n_markets]

    if not markets:
        return []

    print(f"  discovering from {len(markets)} top-volume markets…")

    # Holders fetch with concurrency limit
    sem = asyncio.Semaphore(market_concurrency)

    async def fetch_one(market: dict) -> list[dict]:
        cid = market.get("conditionId")
        if not cid:
            return []
        async with sem:
            try:
                data = await client.get_market_holders(cid, limit=holders_per_market)
            except Exception:
                return []
        # /holders returns list of {token, holders: [...]} per outcome
        market_slug = market.get("slug", "")[:30]
        out: list[dict] = []
        if isinstance(data, list):
            for token_block in data:
                holders = token_block.get("holders", []) if isinstance(token_block, dict) else []
                for h in holders:
                    if not isinstance(h, dict):
                        continue
                    addr = (h.get("proxyWallet") or h.get("address") or "").lower()
                    if not _is_valid_address(addr):
                        continue
                    # amount is in shares; we don't know price here, but big holders
                    # almost always have $1000+ worth on liquid markets
                    amount = _safe_float(h.get("amount"))
                    if amount < min_holder_size_usd:
                        continue
                    name = (h.get("name") or "").strip()
                    out.append({
                        "address": addr,
                        "label": f"holder:{name[:14] if name else addr[:10]}",
                        "source": f"holders:{market_slug}",
                        "hint": "unknown",
                        "_discovered_amount": amount,
                        "_market_volume": market_volume(market),
                    })
        return out

    results = await asyncio.gather(*[fetch_one(m) for m in markets])
    all_seeds = [s for batch in results for s in batch]

    # Dedupe by address: keep entry with highest discovery amount
    by_addr: dict[str, dict] = {}
    for s in all_seeds:
        a = s["address"]
        if a not in by_addr or s["_discovered_amount"] > by_addr[a]["_discovered_amount"]:
            by_addr[a] = s

    seeds = list(by_addr.values())
    seeds.sort(key=lambda s: s["_discovered_amount"], reverse=True)
    return seeds
