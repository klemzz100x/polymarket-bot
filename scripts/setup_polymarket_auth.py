#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Polymarket API credentials setup.

Generates API key/secret/passphrase from your wallet private key and writes
them to .env. Run this once before using the live execution engine.

The private key never leaves your machine — signing is done locally.

Usage:
    python scripts/setup_polymarket_auth.py
    python scripts/setup_polymarket_auth.py --check   # verify existing creds
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Load .env before anything else
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


CLOB_HOST = "https://clob.polymarket.com"
CHAIN_ID = 137  # Polygon


def get_client():
    from py_clob_client.client import ClobClient

    private_key = os.environ.get("POLYMARKET_PRIVATE_KEY", "")
    funder = os.environ.get("POLYMARKET_FUNDER_ADDRESS", "")

    if not private_key or private_key == "0x<ta_clé_ici>":
        print("ERROR: POLYMARKET_PRIVATE_KEY not set in .env")
        sys.exit(1)
    if not funder:
        print("ERROR: POLYMARKET_FUNDER_ADDRESS not set in .env")
        sys.exit(1)

    return ClobClient(
        host=CLOB_HOST,
        key=private_key,
        chain_id=CHAIN_ID,
        funder=funder,
    )


def write_env_values(updates: dict[str, str]) -> None:
    """Update specific keys in .env without touching other values."""
    lines = env_path.read_text(encoding="utf-8").splitlines()
    updated = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            if k in updates:
                new_lines.append(f"{k}={updates[k]}")
                updated.add(k)
                continue
        new_lines.append(line)
    # Append any keys not already in file
    for k, v in updates.items():
        if k not in updated:
            new_lines.append(f"{k}={v}")
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def cmd_generate(args) -> None:
    print("\n=== Polymarket API Credentials Setup ===\n")

    client = get_client()
    funder = os.environ["POLYMARKET_FUNDER_ADDRESS"]
    print(f"Wallet    : {funder}")
    print(f"CLOB host : {CLOB_HOST}")
    print(f"Chain     : Polygon (137)")
    print()

    # Check if credentials already exist
    existing_key = os.environ.get("POLYMARKET_API_KEY", "")
    if existing_key and not args.force:
        print(f"API key already set: {existing_key[:8]}...")
        print("Use --force to regenerate.")
        print("\nRun --check to verify existing credentials.")
        return

    print("Generating API credentials (signing locally)...")
    try:
        creds = client.create_or_derive_api_creds()
        print(f"  API Key       : {creds.api_key}")
        print(f"  API Secret    : {creds.api_secret[:8]}...")
        print(f"  API Passphrase: {creds.api_passphrase[:6]}...")
    except Exception as exc:
        print(f"\nERROR generating credentials: {exc}")
        print("\nPossible causes:")
        print("  - Private key incorrect or wrong format (must start with 0x)")
        print("  - Network issue (check internet connection)")
        print("  - Funder address mismatch with private key")
        sys.exit(1)

    write_env_values({
        "POLYMARKET_API_KEY": creds.api_key,
        "POLYMARKET_API_SECRET": creds.api_secret,
        "POLYMARKET_API_PASSPHRASE": creds.api_passphrase,
    })
    print("\n.env updated with API credentials.")

    # Verify immediately
    print("\nVerifying credentials against CLOB API...")
    cmd_check(args, client=client, creds=creds)


def cmd_check(args, client=None, creds=None) -> None:
    if client is None:
        client = get_client()

    # When called after generate, creds are passed directly — skip env check
    if creds is None:
        api_key = os.environ.get("POLYMARKET_API_KEY", "")
        if not api_key:
            print("No API key in .env — run setup first (without --check).")
            return

    try:
        from py_clob_client.clob_types import ApiCreds as _ApiCreds
        if creds is None:
            creds = _ApiCreds(
                api_key=os.environ["POLYMARKET_API_KEY"],
                api_secret=os.environ["POLYMARKET_API_SECRET"],
                api_passphrase=os.environ["POLYMARKET_API_PASSPHRASE"],
            )
        from py_clob_client.clob_types import AssetType, BalanceAllowanceParams
        client.set_api_creds(creds)
        ok = client.get_ok()
        bal = client.get_balance_allowance(BalanceAllowanceParams(asset_type=AssetType.COLLATERAL))
        usdc_bal = float(bal.get("balance", 0)) / 1e6 if bal else 0
        print(f"\n  API status   : {ok}")
        print(f"  pUSD balance : {usdc_bal:.2f} USDC")
        print("\n  Credentials VALID.")
    except Exception as exc:
        print(f"\n  ERROR: {exc}")
        print("  Credentials may be expired or invalid — re-run without --check to regenerate.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Setup Polymarket API credentials")
    parser.add_argument("--check", action="store_true", help="Verify existing credentials only")
    parser.add_argument("--force", action="store_true", help="Force regeneration even if creds exist")
    args = parser.parse_args()

    if args.check:
        cmd_check(args)
    else:
        cmd_generate(args)


if __name__ == "__main__":
    main()
