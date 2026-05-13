from typing import Protocol

from polybot.wallet.models import WalletBalance


class BalanceSource(Protocol):
    async def get_balances(self, wallet_address: str) -> list[WalletBalance]:
        ...


class BalanceSync:
    def __init__(self, source: BalanceSource) -> None:
        self.source = source

    async def sync(self, wallet_address: str) -> list[WalletBalance]:
        return await self.source.get_balances(wallet_address)
