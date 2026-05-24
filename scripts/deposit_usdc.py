#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Deposit USDC to Polymarket on Polygon.

Workflow:
  1. Check USDC.e + native USDC + POL balances
  2. (Optional) Swap native USDC -> USDC.e via Uniswap V3
  3. Approve USDC.e to Polymarket exchange contracts
  4. Sync allowance state with CLOB API

Usage:
    # Check balances only
    PYTHONPATH=src python scripts/deposit_usdc.py --check

    # Swap native USDC -> USDC.e (on-chain, costs ~$0.01 in POL)
    PYTHONPATH=src python scripts/deposit_usdc.py --swap --amount 20.0

    # Approve USDC.e to Polymarket contracts (after swap)
    PYTHONPATH=src python scripts/deposit_usdc.py --approve

    # Full flow: swap + approve in one go
    PYTHONPATH=src python scripts/deposit_usdc.py --swap --approve --amount 20.0

    # Dry-run any of the above (no tx sent)
    PYTHONPATH=src python scripts/deposit_usdc.py --swap --approve --amount 20.0 --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# ── Load .env ─────────────────────────────────────────────────────────────────
_env = Path(__file__).parent.parent / ".env"
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            k, _, v = _line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

PRIVATE_KEY = os.environ.get("POLYMARKET_PRIVATE_KEY", "")
FUNDER_ADDRESS = os.environ.get("POLYMARKET_FUNDER_ADDRESS", "")
API_KEY = os.environ.get("POLYMARKET_API_KEY", "")
API_SECRET = os.environ.get("POLYMARKET_API_SECRET", "")
API_PASSPHRASE = os.environ.get("POLYMARKET_API_PASSPHRASE", "")
CLOB_URL = os.environ.get("POLYMARKET_CLOB_API_URL", "https://clob.polymarket.com")

# ── Polygon constants ──────────────────────────────────────────────────────────
POLYGON_RPCS = [
    "https://polygon-bor-rpc.publicnode.com",
    "https://polygon-rpc.com",
    "https://rpc.ankr.com/polygon",
    "https://polygon.llamarpc.com",
]
POLYGON_CHAIN_ID = 137

# USDC.e — the bridged USDC that Polymarket uses as collateral
USDCE_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
# Native USDC — Circle's newer token (what's in the wallet)
USDC_NATIVE_ADDRESS = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
USDC_DECIMALS = 6

# Exchange contracts that need USDC.e approval.
# Source: get_balance_allowance() API response.
EXCHANGE_CONTRACTS = [
    ("CTF Exchange",          "0xE111180000d2663C0091e4f400237545B87B996B"),
    ("Neg Risk CTF Exchange", "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296"),
    ("Neg Risk Adapter",      "0xe2222d279d744050d28e00520010520000310F59"),
]

# Uniswap V3 SwapRouter on Polygon (same address as mainnet)
UNISWAP_V3_ROUTER = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
# Stable pool fee tier: 500 = 0.05% (USDC / USDC.e pair)
STABLE_FEE_TIER = 500

MAX_UINT256 = 2**256 - 1

ERC20_ABI = json.loads("""[
  {"name":"balanceOf","type":"function","stateMutability":"view",
   "inputs":[{"name":"owner","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
  {"name":"allowance","type":"function","stateMutability":"view",
   "inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],
   "outputs":[{"name":"","type":"uint256"}]},
  {"name":"approve","type":"function","stateMutability":"nonpayable",
   "inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],
   "outputs":[{"name":"","type":"bool"}]}
]""")

UNISWAP_ROUTER_ABI = json.loads("""[
  {
    "name": "exactInputSingle",
    "type": "function",
    "stateMutability": "payable",
    "inputs": [{
      "components": [
        {"name":"tokenIn","type":"address"},
        {"name":"tokenOut","type":"address"},
        {"name":"fee","type":"uint24"},
        {"name":"recipient","type":"address"},
        {"name":"deadline","type":"uint256"},
        {"name":"amountIn","type":"uint256"},
        {"name":"amountOutMinimum","type":"uint256"},
        {"name":"sqrtPriceLimitX96","type":"uint160"}
      ],
      "name":"params",
      "type":"tuple"
    }],
    "outputs":[{"name":"amountOut","type":"uint256"}]
  }
]""")


def sep(n=70):
    print("-" * n)


def connect_polygon(rpc_override=None):
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware

    rpc_list = [rpc_override] if rpc_override else POLYGON_RPCS
    for rpc_url in rpc_list:
        print(f"  Trying: {rpc_url} ...", end=" ", flush=True)
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        if w3.is_connected():
            print("OK")
            return w3
        print("failed")
    print("\nERROR: All Polygon RPC endpoints unreachable. Check your internet.")
    sys.exit(1)


def get_token_balance(w3, token_addr, wallet):
    c = w3.eth.contract(address=w3.to_checksum_address(token_addr), abi=ERC20_ABI)
    raw = c.functions.balanceOf(w3.to_checksum_address(wallet)).call()
    return raw / 10**USDC_DECIMALS


def get_allowance(w3, token_addr, owner, spender):
    c = w3.eth.contract(address=w3.to_checksum_address(token_addr), abi=ERC20_ABI)
    raw = c.functions.allowance(
        w3.to_checksum_address(owner), w3.to_checksum_address(spender)
    ).call()
    return raw / 10**USDC_DECIMALS


def send_tx(w3, tx, private_key, dry_run, label=""):
    try:
        tx["gas"] = w3.eth.estimate_gas(tx)
    except Exception:
        tx["gas"] = 80_000

    gas_pol = (tx["gas"] * tx["gasPrice"]) / 1e18
    print(f"    Gas: ~{tx['gas']:,} units, cost ~{gas_pol:.6f} POL")

    if dry_run:
        print("    [DRY-RUN] Not sent.")
        return None

    signed = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    hex_hash = tx_hash.hex()
    print(f"    TX: {hex_hash}")
    print(f"    Polygonscan: https://polygonscan.com/tx/{hex_hash}")
    print("    Waiting...", end=" ", flush=True)
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        status = "SUCCESS" if receipt.status == 1 else "FAILED"
        print(f"{status} (block #{receipt.blockNumber:,})")
    except Exception as e:
        print(f"Timeout: {e}")
    return hex_hash


def do_approve(w3, private_key, wallet, token_addr, spender, amount_raw, dry_run):
    c = w3.eth.contract(address=w3.to_checksum_address(token_addr), abi=ERC20_ABI)
    nonce = w3.eth.get_transaction_count(w3.to_checksum_address(wallet))
    tx = c.functions.approve(
        w3.to_checksum_address(spender), amount_raw
    ).build_transaction({
        "chainId": POLYGON_CHAIN_ID,
        "from": w3.to_checksum_address(wallet),
        "nonce": nonce,
        "gasPrice": w3.eth.gas_price,
    })
    return send_tx(w3, tx, private_key, dry_run)


def do_swap_usdc_to_usdce(w3, private_key, wallet, amount_in_raw, dry_run):
    """Swap native USDC -> USDC.e via Uniswap V3 (0.05% fee tier)."""
    if dry_run:
        amount = amount_in_raw / 10**USDC_DECIMALS
        print(f"    [DRY-RUN] Would swap ${amount:.2f} native USDC -> USDC.e via Uniswap V3")
        print(f"    [DRY-RUN] Router: {UNISWAP_V3_ROUTER} | fee: {STABLE_FEE_TIER} | slippage: 0.5%")
        return None

    router = w3.eth.contract(
        address=w3.to_checksum_address(UNISWAP_V3_ROUTER), abi=UNISWAP_ROUTER_ABI
    )
    deadline = int(time.time()) + 600  # 10 min
    amount_out_min = int(amount_in_raw * 0.995)  # 0.5% max slippage

    nonce = w3.eth.get_transaction_count(w3.to_checksum_address(wallet))
    tx = router.functions.exactInputSingle((
        w3.to_checksum_address(USDC_NATIVE_ADDRESS),
        w3.to_checksum_address(USDCE_ADDRESS),
        STABLE_FEE_TIER,
        w3.to_checksum_address(wallet),
        deadline,
        amount_in_raw,
        amount_out_min,
        0,
    )).build_transaction({
        "chainId": POLYGON_CHAIN_ID,
        "from": w3.to_checksum_address(wallet),
        "nonce": nonce,
        "gasPrice": w3.eth.gas_price,
        "value": 0,
    })
    return send_tx(w3, tx, private_key, dry_run, label="Swap USDC->USDC.e")


def sync_clob(dry_run):
    if dry_run:
        print("  [DRY-RUN] CLOB sync skipped.")
        return
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds, AssetType, BalanceAllowanceParams

        client = ClobClient(
            host=CLOB_URL, key=PRIVATE_KEY, chain_id=POLYGON_CHAIN_ID, funder=FUNDER_ADDRESS
        )
        client.set_api_creds(ApiCreds(
            api_key=API_KEY, api_secret=API_SECRET, api_passphrase=API_PASSPHRASE
        ))
        for asset in [AssetType.COLLATERAL, AssetType.CONDITIONAL]:
            try:
                client.update_balance_allowance(BalanceAllowanceParams(asset_type=asset))
            except Exception as e:
                print(f"  [WARN] sync {asset}: {e}")
        raw = client.get_balance_allowance(BalanceAllowanceParams(asset_type=AssetType.COLLATERAL))
        bal = float(raw.get("balance", 0)) / 1e6
        print(f"  CLOB pUSD balance: ${bal:.6f}")
    except Exception as e:
        print(f"  [WARN] CLOB sync failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Deposit USDC to Polymarket on Polygon")
    parser.add_argument("--check", action="store_true", help="Show balances only (default)")
    parser.add_argument("--swap", action="store_true", help="Swap native USDC -> USDC.e via Uniswap V3")
    parser.add_argument("--approve", action="store_true", help="Approve USDC.e to exchange contracts")
    parser.add_argument("--amount", type=float, default=None,
                        help="USDC amount to swap/approve (default: full balance)")
    parser.add_argument("--dry-run", action="store_true", help="Build txs but don't send")
    parser.add_argument("--rpc", default=None, help="Override Polygon RPC URL")
    args = parser.parse_args()

    if not args.swap and not args.approve:
        args.check = True

    if not PRIVATE_KEY or not FUNDER_ADDRESS:
        print("ERROR: POLYMARKET_PRIVATE_KEY and POLYMARKET_FUNDER_ADDRESS must be set in .env")
        sys.exit(1)

    print("\nConnecting to Polygon...")
    w3 = connect_polygon(args.rpc)
    block = w3.eth.block_number
    print(f"Block #{block:,}")

    wallet = FUNDER_ADDRESS
    sep()
    print(f"Wallet: {wallet}")
    sep()

    # ── [1] Balances ───────────────────────────────────────────────────────────
    print("\n[1] Balances")
    usdce_bal = get_token_balance(w3, USDCE_ADDRESS, wallet)
    native_bal = get_token_balance(w3, USDC_NATIVE_ADDRESS, wallet)
    pol_bal = w3.eth.get_balance(w3.to_checksum_address(wallet)) / 1e18

    print(f"  USDC.e  (Polymarket collateral): ${usdce_bal:.6f}")
    print(f"  USDC    (native, Circle):         ${native_bal:.6f}")
    print(f"  POL     (gas):                    {pol_bal:.6f} POL")

    if pol_bal < 0.001:
        print("\n  WARNING: Very low POL balance. Need ~0.01 POL for gas.")
        print("           Send POL to your wallet from an exchange (Binance, Kraken...).")

    if native_bal > 0 and usdce_bal < 1.0:
        print(f"\n  INFO: You have ${native_bal:.2f} native USDC but Polymarket needs USDC.e.")
        if not args.swap:
            print("        Run with --swap to convert automatically.")

    # ── [2] USDC.e allowances ──────────────────────────────────────────────────
    print("\n[2] USDC.e allowances (exchange contracts)")
    for name, addr in EXCHANGE_CONTRACTS:
        current = get_allowance(w3, USDCE_ADDRESS, wallet, addr)
        status = "OK" if current >= 1.0 else "needs approval"
        print(f"  {name:<30} {current:.2f} USDC.e  [{status}]")

    if args.check:
        print("\n[--check] Done. No transactions sent.")
        return

    # ── [3] Swap native USDC -> USDC.e ────────────────────────────────────────
    if args.swap:
        print("\n[3] Swap native USDC -> USDC.e")
        if native_bal == 0:
            print("  No native USDC to swap.")
        else:
            amount = args.amount if args.amount is not None else native_bal
            amount = min(amount, native_bal)
            amount_raw = int(amount * 10**USDC_DECIMALS)
            print(f"  Swapping ${amount:.2f} native USDC -> USDC.e via Uniswap V3 (0.05% fee)...")

            # Step 3a: approve native USDC to Uniswap router
            current_allowance = get_allowance(w3, USDC_NATIVE_ADDRESS, wallet, UNISWAP_V3_ROUTER)
            if current_allowance < amount:
                print(f"  Step 3a: Approve ${amount:.2f} native USDC to Uniswap V3 Router...")
                do_approve(w3, PRIVATE_KEY, wallet, USDC_NATIVE_ADDRESS, UNISWAP_V3_ROUTER, amount_raw, args.dry_run)
                if not args.dry_run:
                    time.sleep(2)
            else:
                print(f"  Step 3a: Uniswap Router already approved ({current_allowance:.2f} USDC) — skip")

            # Step 3b: execute swap
            print(f"  Step 3b: Swap ${amount:.2f} native USDC -> USDC.e...")
            do_swap_usdc_to_usdce(w3, PRIVATE_KEY, wallet, amount_raw, args.dry_run)
            if not args.dry_run:
                time.sleep(3)
                usdce_bal = get_token_balance(w3, USDCE_ADDRESS, wallet)
                print(f"  New USDC.e balance: ${usdce_bal:.6f}")

    # ── [4] Approve USDC.e to exchange contracts ───────────────────────────────
    if args.approve:
        print("\n[4] Approve USDC.e to Polymarket exchange contracts")

        # Refresh balance after potential swap
        usdce_bal = get_token_balance(w3, USDCE_ADDRESS, wallet)

        # In dry-run with --swap: simulate as if swap succeeded
        if usdce_bal < 0.01 and args.dry_run and args.swap:
            usdce_bal = args.amount or 20.0
            print(f"  [DRY-RUN] Assuming ${usdce_bal:.2f} USDC.e after swap...")

        if usdce_bal < 0.01 and not args.dry_run:
            print("  ERROR: No USDC.e to approve. Run --swap first or bridge USDC.e to this wallet.")
            sys.exit(1)

        amount_raw = MAX_UINT256  # unlimited approval — standard for trading bots

        for name, addr in EXCHANGE_CONTRACTS:
            current = get_allowance(w3, USDCE_ADDRESS, wallet, addr)
            print(f"\n  -> {name}")
            print(f"     Contract: {addr}")
            print(f"     Current allowance: ${current:.2f}")

            if current >= usdce_bal and current > 100:
                print("     Already approved — skipping.")
                continue

            do_approve(w3, PRIVATE_KEY, wallet, USDCE_ADDRESS, addr, amount_raw, args.dry_run)
            if not args.dry_run:
                time.sleep(2)

        # ── [5] CLOB sync ──────────────────────────────────────────────────────
        print("\n[5] Sync with Polymarket CLOB API...")
        sync_clob(args.dry_run)

    sep()
    if args.dry_run:
        print("DRY-RUN complete. Re-run without --dry-run to execute.")
    else:
        print("Done. Verify at: https://polygonscan.com/address/" + wallet)
        if args.approve:
            print("Next: place a test order via setup_polymarket_auth.py --check")


if __name__ == "__main__":
    main()
