from typing import Protocol

from polybot.wallet.models import OpenOrderState


class OpenOrderSource(Protocol):
    async def get_open_orders(self, wallet_address: str) -> list[OpenOrderState]:
        ...


class OpenOrderSync:
    def __init__(self, source: OpenOrderSource) -> None:
        self.source = source

    async def sync(self, wallet_address: str) -> list[OpenOrderState]:
        return await self.source.get_open_orders(wallet_address)
