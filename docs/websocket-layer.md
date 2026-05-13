# WebSocket Layer

The WebSocket Layer improves market microstructure granularity without enabling live trading.

## Goals

- Stream orderbook updates.
- Stream trade updates.
- Reconnect automatically.
- Send heartbeat messages.
- Auto-resubscribe after reconnect.
- Store events in Postgres and Redis.
- Feed the same validation, metrics, signals, backtests, and paper-trading pipeline.

## Modules

- `src/polybot/polymarket/websocket/client.py`: resilient market WebSocket client.
- `src/polybot/polymarket/websocket/collector.py`: stores orderbook and trade events.

## Client Behavior

The client:
- connects to `<POLYMARKET_WS_URL>/market`,
- subscribes with `assets_ids`,
- ignores `PONG`,
- parses JSON messages,
- reconnects with backoff,
- resubscribes after reconnect,
- filters orderbook and trade events.

## Storage Rule

WebSocket data must still flow through:

```text
WebSocket event -> normalization -> Postgres -> Redis -> validation/research
```

Postgres remains the quantitative source of truth.

## Safety

This layer has no order placement code. It prepares better research data and future real-time systems only.
