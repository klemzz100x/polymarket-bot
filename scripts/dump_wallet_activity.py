#!/usr/bin/env python
"""Tiny diagnostic: dump raw /activity sample for one wallet."""
from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter

from polybot.core.config import get_settings
from polybot.polymarket.api import PolymarketClient


async def main():
    addr = sys.argv[1] if len(sys.argv) > 1 else "0x5bffcf561bcae83af680ad600cb99f1184d6ffbe"
    settings = get_settings()
    async with PolymarketClient(settings) as client:
        activity = await client.get_wallet_activity(addr, limit=20)
        positions = await client.get_wallet_positions(addr, limit=5)

    print(f"=== {addr} ===")
    print(f"activity: {len(activity)} rows")
    if activity:
        # Show all unique field names
        keys = set()
        for a in activity[:50]:
            if isinstance(a, dict):
                keys.update(a.keys())
        print(f"\nActivity field union: {sorted(keys)}")

        # Show event types
        types = Counter(a.get("type") or a.get("event_type") for a in activity if isinstance(a, dict))
        print(f"Type distribution: {dict(types)}")

        # Dump first 2 activity rows
        print("\nFirst 2 activity rows:")
        for a in activity[:2]:
            print(json.dumps(a, indent=2, default=str)[:1500])
            print("---")

    print(f"\npositions: {len(positions)} rows")
    if positions:
        keys = set()
        for p in positions[:5]:
            if isinstance(p, dict):
                keys.update(p.keys())
        print(f"Position field union: {sorted(keys)}")
        print("\nFirst position row:")
        if positions:
            print(json.dumps(positions[0], indent=2, default=str)[:1500])


if __name__ == "__main__":
    asyncio.run(main())
