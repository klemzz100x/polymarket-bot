# Wallet Integration

The wallet layer is designed for a dedicated bot wallet only.

Do not use a principal wallet. Do not hardcode private keys.

## Modules

- `wallet_manager.py`: orchestrates sync.
- `balance_sync.py`: reads balances.
- `position_sync.py`: reads positions.
- `order_sync.py`: reads open orders.
- `wallet_health.py`: detects missing or degraded wallet state.
- `signer.py`: safe signer shell; signing is disabled unless explicitly wired later.

## Models

- `WalletBalance`
- `WalletPosition`
- `WalletSnapshot`
- `OpenOrderState`
- `WalletHealthStatus`

## Storage

Snapshots are stored in `app.wallet_snapshots`.

## Safety

The current implementation is read-only. The signer does not expose secrets and refuses signing unless explicitly enabled by future code.
