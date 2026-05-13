from polybot.wallet.balance_sync import BalanceSource, BalanceSync
from polybot.wallet.models import WalletHealthStatus, WalletSnapshot, now_utc
from polybot.wallet.order_sync import OpenOrderSource, OpenOrderSync
from polybot.wallet.position_sync import PositionSource, PositionSync
from polybot.wallet.wallet_health import build_wallet_health


class WalletManager:
    def __init__(
        self,
        *,
        wallet_address: str,
        balance_source: BalanceSource,
        position_source: PositionSource,
        order_source: OpenOrderSource,
    ) -> None:
        self.wallet_address = wallet_address
        self.balance_sync = BalanceSync(balance_source)
        self.position_sync = PositionSync(position_source)
        self.order_sync = OpenOrderSync(order_source)

    async def sync_snapshot(self) -> WalletSnapshot:
        balances = await self.balance_sync.sync(self.wallet_address)
        positions = await self.position_sync.sync(self.wallet_address)
        open_orders = await self.order_sync.sync(self.wallet_address)
        return WalletSnapshot(
            wallet_address=self.wallet_address,
            captured_at=now_utc(),
            balances=balances,
            positions=positions,
            open_orders=open_orders,
        )

    async def health(self) -> WalletHealthStatus:
        if not self.wallet_address:
            return build_wallet_health(None, wallet_address=self.wallet_address)
        try:
            snapshot = await self.sync_snapshot()
        except Exception:
            return build_wallet_health(None, wallet_address=self.wallet_address)
        return build_wallet_health(snapshot, wallet_address=self.wallet_address)
