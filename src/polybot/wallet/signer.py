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
