#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio

from polybot.core.config import get_settings
from polybot.data.storage.database import create_session_factory
from polybot.exchange import PolymarketAdapter
from polybot.knowledge.obsidian import ObsidianVault
from polybot.live_execution.modes import mode_allows_wallet_sync, parse_live_execution_mode
from polybot.wallet import WalletManager
from polybot.wallet.storage import WalletSnapshotRepository


async def run() -> int:
    parser = argparse.ArgumentParser(description="Sync dedicated bot wallet state in read-only mode.")
    parser.add_argument("--persist-db", action="store_true")
    parser.add_argument("--obsidian", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    mode = parse_live_execution_mode(settings.live_execution_mode)
    if not mode_allows_wallet_sync(mode):
        print(f"Wallet sync blocked in mode={mode.value}. Use READ_ONLY, SHADOW, or MICRO_LIVE.")
        return 1
    wallet_address = settings.polymarket_funder_address
    adapter = PolymarketAdapter(settings=settings)
    manager = WalletManager(
        wallet_address=wallet_address,
        balance_source=adapter,
        position_source=adapter,
        order_source=adapter,
    )
    snapshot = await manager.sync_snapshot()
    print(f"Wallet={snapshot.wallet_address or 'missing'}")
    print(f"Balances={len(snapshot.balances)} Positions={len(snapshot.positions)} OpenOrders={len(snapshot.open_orders)}")
    print(f"Exposure={snapshot.total_exposure_usd}")

    if args.persist_db:
        session_factory = create_session_factory(settings.database_url)
        async with session_factory() as session:
            await WalletSnapshotRepository(session).insert_snapshot(snapshot)
            await session.commit()
        print("Persisted wallet snapshot.")

    if args.obsidian:
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()
        path = vault.write_note(
            "Live-Execution",
            "Wallet Sync Report",
            _render_wallet_snapshot(snapshot),
            overwrite=True,
        )
        print(f"Obsidian={path}")
    return 0


def _render_wallet_snapshot(snapshot) -> str:
    return f"""# Wallet Sync Report

## Executive Summary
- Wallet: `{snapshot.wallet_address or "missing"}`
- Balances: `{len(snapshot.balances)}`
- Positions: `{len(snapshot.positions)}`
- Open orders: `{len(snapshot.open_orders)}`
- Exposure USD: `{snapshot.total_exposure_usd}`

## Wallet
Dedicated bot wallet only. Do not use a principal wallet.

## Balances
{snapshot.balances or "No balances returned by the current adapter."}

## Positions
{snapshot.positions or "No positions returned by the current adapter."}

## Open Orders
{snapshot.open_orders or "No open orders returned by the current adapter."}

## Next Actions
- Keep this layer read-only until readiness and risk gates are proven.
- Wire a real private client only after dedicated wallet testing.

## Links
[[Live Readiness]]
[[OMS]]
[[Risk Management]]
"""


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
