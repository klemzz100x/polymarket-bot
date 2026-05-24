from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SignerConfig:
    wallet_address: str = ""
    private_key_configured: bool = False


class SafeSigner:
    """Signer placeholder that never exposes secrets and never signs unless explicitly enabled."""

    def __init__(self, config: SignerConfig, *, signing_enabled: bool = False) -> None:
        self.config = config
        self.signing_enabled = signing_enabled

    def health(self) -> dict[str, object]:
        return {
            "wallet_address": self.config.wallet_address,
            "private_key_configured": self.config.private_key_configured,
            "signing_enabled": self.signing_enabled,
        }

    def sign_order_payload(self, _payload: dict[str, object]) -> str:
        if not self.signing_enabled:
            raise PermissionError("signing_disabled")
        raise NotImplementedError("live_signer_not_configured")


class LiveSigner:
    """Live order signer backed by py-clob-client (CLOB V2).

    Private key and credentials are loaded from env or passed explicitly.
    Signing is done locally — private key never leaves the machine.
    """

    def __init__(
        self,
        private_key: str,
        funder_address: str,
        api_key: str,
        api_secret: str,
        api_passphrase: str,
        *,
        host: str = "https://clob.polymarket.com",
        chain_id: int = 137,
    ) -> None:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds

        self._funder = funder_address
        self._client = ClobClient(host=host, key=private_key, chain_id=chain_id, funder=funder_address)
        self._client.set_api_creds(
            ApiCreds(api_key=api_key, api_secret=api_secret, api_passphrase=api_passphrase)
        )

    @classmethod
    def from_env(cls) -> "LiveSigner":
        """Instantiate from environment variables (loaded from .env)."""
        required = [
            "POLYMARKET_PRIVATE_KEY",
            "POLYMARKET_FUNDER_ADDRESS",
            "POLYMARKET_API_KEY",
            "POLYMARKET_API_SECRET",
            "POLYMARKET_API_PASSPHRASE",
        ]
        missing = [k for k in required if not os.environ.get(k)]
        if missing:
            raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}")
        return cls(
            private_key=os.environ["POLYMARKET_PRIVATE_KEY"],
            funder_address=os.environ["POLYMARKET_FUNDER_ADDRESS"],
            api_key=os.environ["POLYMARKET_API_KEY"],
            api_secret=os.environ["POLYMARKET_API_SECRET"],
            api_passphrase=os.environ["POLYMARKET_API_PASSPHRASE"],
        )

    # ── Status ────────────────────────────────────────────────────────────────

    def health(self) -> dict:
        """Check API connectivity. Returns {"ok": True, "funder": ...}."""
        ok = self._client.get_ok()
        return {"ok": ok, "funder": self._funder}

    def get_balance(self) -> dict:
        """Return USDC/pUSD balance and allowance."""
        from py_clob_client.clob_types import AssetType, BalanceAllowanceParams
        raw = self._client.get_balance_allowance(BalanceAllowanceParams(asset_type=AssetType.COLLATERAL))
        # balance is in micro-USDC (6 decimals) — convert to human-readable
        usdc = float(raw.get("balance", 0)) / 1e6
        return {"balance_usdc": usdc, "raw": raw}

    # ── Order lifecycle ───────────────────────────────────────────────────────

    def create_limit_order(
        self,
        *,
        token_id: str,
        side: str,    # "BUY" or "SELL"
        price: float, # 0.01 – 0.99
        size: float,  # in shares
    ) -> dict:
        """Build and sign a limit order. Returns the signed order (not yet submitted)."""
        from py_clob_client.clob_types import OrderArgs

        return self._client.create_order(OrderArgs(
            token_id=token_id,
            price=price,
            size=size,
            side=side.upper(),
        ))

    def submit_order(
        self,
        signed_order: dict,
        *,
        time_in_force: str = "GTC",
        post_only: bool = True,
    ) -> dict:
        """Submit a pre-signed order. orderType and post_only go here, not in OrderArgs."""
        from py_clob_client.clob_types import OrderType

        tif_map = {
            "GTC": OrderType.GTC,
            "GTD": OrderType.GTD,
            "FOK": OrderType.FOK,
            "FAK": OrderType.FAK,
        }
        return self._client.post_order(
            signed_order,
            orderType=tif_map.get(time_in_force.upper(), OrderType.GTC),
            post_only=post_only,
        )

    def place_limit_order(
        self,
        *,
        token_id: str,
        side: str,
        price: float,
        size: float,
        time_in_force: str = "GTC",
        post_only: bool = True,
    ) -> dict:
        """Convenience: create + submit in one call."""
        signed = self.create_limit_order(token_id=token_id, side=side, price=price, size=size)
        return self.submit_order(signed, time_in_force=time_in_force, post_only=post_only)

    def cancel_order(self, order_id: str) -> dict:
        """Cancel a single open order by order_id."""
        return self._client.cancel(order_id)

    def get_open_orders(self, *, market: str | None = None) -> list:
        """List open orders, optionally filtered by market (condition_id)."""
        params = {}
        if market:
            params["market"] = market
        return self._client.get_orders(**params)

    def cancel_all(self) -> dict:
        """Emergency kill — cancel all open orders across all markets."""
        return self._client.cancel_all()
