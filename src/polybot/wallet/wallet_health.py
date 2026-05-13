from polybot.wallet.models import WalletHealthStatus, WalletSnapshot, now_utc


def build_wallet_health(snapshot: WalletSnapshot | None, *, wallet_address: str) -> WalletHealthStatus:
    warnings: list[str] = []
    connected = snapshot is not None
    if not wallet_address:
        warnings.append("wallet_address_missing")
    if snapshot is not None and not snapshot.balances:
        warnings.append("no_balances_returned")
    if snapshot is not None and snapshot.total_exposure_usd > 0 and not snapshot.positions:
        warnings.append("exposure_without_positions")
    status = "ok" if connected and not warnings else ("warning" if connected else "critical")
    return WalletHealthStatus(
        wallet_address=wallet_address,
        generated_at=now_utc(),
        connected=connected,
        status=status,
        warnings=warnings,
    )
