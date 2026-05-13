from typing import Any


class PolymarketMarketAPI:
    def __init__(self, client: Any) -> None:
        self.client = client

    async def get_market(self, market_id: str) -> dict[str, Any]:
        return await self.client.get_market_by_id(market_id)

    async def get_orderbook(self, token_id: str) -> dict[str, Any]:
        return await self.client.get_orderbook(token_id)
