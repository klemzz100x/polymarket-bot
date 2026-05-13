from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from polybot.wallet.models import WalletSnapshot


class WalletSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_snapshot(self, snapshot: WalletSnapshot) -> None:
        await self.session.execute(
            text(
                """
                INSERT INTO app.wallet_snapshots (
                    wallet_address, captured_at, total_exposure_usd,
                    balances, positions, open_orders, snapshot
                )
                VALUES (
                    :wallet_address, :captured_at, :total_exposure_usd,
                    CAST(:balances AS JSONB), CAST(:positions AS JSONB),
                    CAST(:open_orders AS JSONB), CAST(:snapshot AS JSONB)
                )
                """
            ),
            {
                "wallet_address": snapshot.wallet_address,
                "captured_at": snapshot.captured_at,
                "total_exposure_usd": snapshot.total_exposure_usd,
                "balances": _json_list([item.to_dict() for item in snapshot.balances]),
                "positions": _json_list([item.to_dict() for item in snapshot.positions]),
                "open_orders": _json_list([item.to_dict() for item in snapshot.open_orders]),
                "snapshot": snapshot.to_json(),
            },
        )

    async def latest_snapshot(self, wallet_address: str | None = None) -> dict | None:
        query = """
            SELECT *
            FROM app.wallet_snapshots
            WHERE (:wallet_address IS NULL OR wallet_address = :wallet_address)
            ORDER BY captured_at DESC
            LIMIT 1
        """
        row = (
            await self.session.execute(text(query), {"wallet_address": wallet_address})
        ).mappings().first()
        return dict(row) if row else None


def _json_list(items: list[dict]) -> str:
    import json

    return json.dumps(items, default=str)
