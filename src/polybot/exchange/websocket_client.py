from dataclasses import dataclass


@dataclass(slots=True)
class ExchangeWebSocketState:
    connected: bool = False
    last_error: str = ""
    subscribed_assets: list[str] | None = None


class PolymarketExchangeWebSocketClient:
    """Execution-side WebSocket placeholder; market-data WebSocket lives separately."""

    def __init__(self) -> None:
        self.state = ExchangeWebSocketState(subscribed_assets=[])

    async def connect(self) -> ExchangeWebSocketState:
        self.state.connected = False
        self.state.last_error = "execution_websocket_not_configured"
        return self.state

    async def close(self) -> None:
        self.state.connected = False
