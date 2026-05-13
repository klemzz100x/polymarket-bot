from typing import Protocol

from polybot.wallet.models import WalletPosition


class PositionSource(Protocol):
    async def get_positions(self, wallet_address: str) -> list[WalletPosition]:
        ...


class PositionSync:
    def __init__(self, source: PositionSource) -> None:
        self.source = source

    async def sync(self, wallet_address: str) -> list[WalletPosition]:
        return await self.source.get_positions(wallet_address)
