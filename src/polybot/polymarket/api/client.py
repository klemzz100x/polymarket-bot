from collections.abc import Sequence
from typing import Any

import httpx

from polybot.core.config import Settings
from polybot.core.logging import get_logger

logger = get_logger(__name__)


class PolymarketClientError(RuntimeError):
    pass


class PolymarketClient:
    """Read-only client for Gamma, Data API, and CLOB public endpoints."""

    def __init__(self, settings: Settings, http_client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self._client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(settings.polymarket_http_timeout_seconds),
            headers={"User-Agent": f"{settings.app_name}/0.1 data-layer"},
        )
        self._owns_client = http_client is None

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "PolymarketClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()

    async def list_markets(
        self,
        *,
        active: bool | None = True,
        closed: bool | None = False,
        limit: int | None = None,
        offset: int = 0,
        enable_order_book: bool | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "limit": limit or self.settings.polymarket_markets_page_limit,
            "offset": offset,
        }
        if active is not None:
            params["active"] = str(active).lower()
        if closed is not None:
            params["closed"] = str(closed).lower()
        if enable_order_book is not None:
            params["enableOrderBook"] = str(enable_order_book).lower()
        data = await self._get(self.settings.polymarket_gamma_api_url, "/markets", params=params)
        if not isinstance(data, list):
            raise PolymarketClientError("Gamma /markets response is not a list")
        return [item for item in data if isinstance(item, dict)]

    async def get_market_by_id(self, market_id: str) -> dict[str, Any]:
        data = await self._get(self.settings.polymarket_gamma_api_url, f"/markets/{market_id}")
        if not isinstance(data, dict):
            raise PolymarketClientError(f"Gamma market {market_id} response is not an object")
        return data

    async def get_orderbook(self, token_id: str) -> dict[str, Any]:
        data = await self._get(
            self.settings.polymarket_clob_api_url,
            "/book",
            params={"token_id": token_id},
        )
        if not isinstance(data, dict):
            raise PolymarketClientError("CLOB /book response is not an object")
        return data

    async def get_orderbooks(self, token_ids: Sequence[str]) -> list[dict[str, Any]]:
        body = [{"token_id": token_id} for token_id in token_ids]
        data = await self._post(self.settings.polymarket_clob_api_url, "/books", json=body)
        if not isinstance(data, list):
            raise PolymarketClientError("CLOB /books response is not a list")
        return [item for item in data if isinstance(item, dict)]

    async def get_public_trades(
        self,
        *,
        markets: Sequence[str] | None = None,
        user: str | None = None,
        limit: int = 100,
        offset: int = 0,
        taker_only: bool | None = None,
        side: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if markets:
            params["market"] = ",".join(markets)
        if user:
            params["user"] = user
        if taker_only is not None:
            params["takerOnly"] = str(taker_only).lower()
        if side:
            params["side"] = side
        data = await self._get(self.settings.polymarket_data_api_url, "/trades", params=params)
        if not isinstance(data, list):
            raise PolymarketClientError("Data API /trades response is not a list")
        return [item for item in data if isinstance(item, dict)]

    async def get_price_history(
        self,
        *,
        token_id: str,
        start_ts: int | None = None,
        end_ts: int | None = None,
        interval: str | None = None,
        fidelity: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"market": token_id}
        if start_ts is not None:
            params["startTs"] = start_ts
        if end_ts is not None:
            params["endTs"] = end_ts
        if interval is not None:
            params["interval"] = interval
        if fidelity is not None:
            params["fidelity"] = fidelity
        data = await self._get(self.settings.polymarket_clob_api_url, "/prices-history", params=params)
        if not isinstance(data, dict):
            raise PolymarketClientError("CLOB /prices-history response is not an object")
        return data

    async def _get(
        self,
        base_url: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = _join_url(base_url, path)
        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.error("polymarket_get_failed", url=url, params=params or {}, error=str(exc))
            raise PolymarketClientError(str(exc)) from exc

    async def _post(
        self,
        base_url: str,
        path: str,
        json: Any,
    ) -> Any:
        url = _join_url(base_url, path)
        try:
            response = await self._client.post(url, json=json)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.error("polymarket_post_failed", url=url, error=str(exc))
            raise PolymarketClientError(str(exc)) from exc


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"

