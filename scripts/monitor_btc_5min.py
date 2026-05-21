#!/usr/bin/env python
"""Real-time monitoring of BTC 5-minute markets with latency arbitrage detection.

This script:
1. Finds the current/next BTC 5-min market
2. Tracks Binance BTC price in real-time
3. Compares with Polymarket odds to detect latency arbitrage
4. Logs all signals and potential trades (shadow trading mode)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import asyncpg
import httpx

from polybot.core.compat import UTC
from polybot.core.config import get_settings
from polybot.core.logging import configure_logging, get_logger
from polybot.data.normalization import normalize_orderbook
from polybot.polymarket.api import PolymarketClient
from polybot.strategies.latency_arbitrage import (
    BinancePriceTracker,
    LatencyArbitrageDetector,
    LatencyArbitrageSignal,
)
from polybot.strategies.pair_arbitrage import (
    PairArbitrageSignal,
    calculate_pair_arbitrage,
)

logger = get_logger(__name__)


@dataclass
class MarketInfo:
    """BTC 5-min market information."""

    condition_id: str
    title: str
    start_time: datetime
    end_time: datetime
    up_token_id: str
    down_token_id: str
    slug: str


@dataclass
class MarketState:
    """Current state of a market."""

    timestamp: datetime
    binance_price: Decimal
    binance_change_30s_pct: Decimal
    up_bid: Decimal | None
    up_ask: Decimal | None
    down_bid: Decimal | None
    down_ask: Decimal | None
    spread: Decimal
    signal: LatencyArbitrageSignal | None = None
    pair_arb_signal: PairArbitrageSignal | None = None


CREATE_MONITOR_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS app.btc_5m_monitor_ticks (
    id BIGSERIAL PRIMARY KEY,
    observed_at TIMESTAMPTZ NOT NULL,
    condition_id TEXT NOT NULL,
    market_slug TEXT NOT NULL,
    market_title TEXT NOT NULL,
    market_start TIMESTAMPTZ,
    market_end TIMESTAMPTZ,
    up_asset_id TEXT NOT NULL,
    down_asset_id TEXT NOT NULL,
    binance_price NUMERIC(38, 18) NOT NULL,
    binance_change_30s_pct NUMERIC(38, 18) NOT NULL DEFAULT 0,
    up_bid NUMERIC(38, 18),
    up_ask NUMERIC(38, 18),
    down_bid NUMERIC(38, 18),
    down_ask NUMERIC(38, 18),
    pair_cost NUMERIC(38, 18),
    spread NUMERIC(38, 18) NOT NULL DEFAULT 0,
    market_state TEXT NOT NULL,
    rejected_reason TEXT NOT NULL DEFAULT '',
    latency_signal JSONB,
    pair_arb_signal JSONB,
    has_latency_signal BOOLEAN NOT NULL DEFAULT false,
    has_pair_arb_signal BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_btc_5m_monitor_ticks_observed
    ON app.btc_5m_monitor_ticks(observed_at DESC);
CREATE INDEX IF NOT EXISTS ix_btc_5m_monitor_ticks_market_observed
    ON app.btc_5m_monitor_ticks(condition_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS ix_btc_5m_monitor_ticks_state_observed
    ON app.btc_5m_monitor_ticks(market_state, observed_at DESC);
"""


async def find_current_btc_5min_market(settings) -> MarketInfo | None:
    """Find the current or next BTC 5-min market."""
    now = datetime.now(UTC)
    current_ts = int(now.timestamp())

    # Try current and next 5-min windows
    timestamps_to_try = [
        ((current_ts // 300)) * 300,  # Current window
        ((current_ts // 300) + 1) * 300,  # Next window
    ]

    async with httpx.AsyncClient(timeout=30) as client:
        for ts in timestamps_to_try:
            slug = f"btc-updown-5m-{ts}"
            url = f"{settings.polymarket_gamma_api_url}/events/slug/{slug}"

            try:
                r = await client.get(url)
                if r.status_code == 200:
                    event = r.json()

                    # Check if market is still active
                    if event.get("closed"):
                        continue

                    market = event["markets"][0]
                    token_ids = json.loads(market["clobTokenIds"])

                    start_time = datetime.fromisoformat(
                        event["startTime"].replace("Z", "+00:00")
                    )
                    end_time = datetime.fromisoformat(
                        event["endDate"].replace("Z", "+00:00")
                    )

                    return MarketInfo(
                        condition_id=market["conditionId"],
                        title=event["title"],
                        start_time=start_time,
                        end_time=end_time,
                        up_token_id=token_ids[0],
                        down_token_id=token_ids[1],
                        slug=slug,
                    )
            except Exception as e:
                logger.debug("market_fetch_error", slug=slug, error=str(e))

    return None


async def get_orderbook_state(
    client: PolymarketClient,
    market: MarketInfo,
) -> tuple[dict, dict]:
    """Get current orderbook state for both UP and DOWN tokens."""
    books = await client.get_orderbooks([market.up_token_id, market.down_token_id])

    up_book = None
    down_book = None

    for book in books:
        asset_id = book.get("asset_id", "")
        if asset_id == market.up_token_id:
            up_book = book
        elif asset_id == market.down_token_id:
            down_book = book

    return up_book or {}, down_book or {}


def extract_best_prices(book: dict) -> tuple[Decimal | None, Decimal | None]:
    """Extract best bid and ask from orderbook."""
    bids = book.get("bids", [])
    asks = book.get("asks", [])

    bid_prices = [Decimal(level["price"]) for level in bids if "price" in level]
    ask_prices = [Decimal(level["price"]) for level in asks if "price" in level]
    best_bid = max(bid_prices) if bid_prices else None
    best_ask = min(ask_prices) if ask_prices else None

    return best_bid, best_ask


async def monitor_market(
    market: MarketInfo,
    settings,
    output_dir: Path,
    interval_ms: int = 500,
    db_conn: asyncpg.Connection | None = None,
    max_seconds: int | None = None,
) -> list[MarketState]:
    """Monitor a single BTC 5-min market until it closes."""
    detector = LatencyArbitrageDetector()
    states: list[MarketState] = []

    # Create output file
    output_file = output_dir / f"{market.slug}.jsonl"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "monitoring_started",
        market=market.title,
        end_time=market.end_time.isoformat(),
        condition_id=market.condition_id[:30],
    )

    stop_at = market.end_time
    if max_seconds is not None:
        stop_at = min(stop_at, datetime.now(UTC) + timedelta(seconds=max_seconds))

    async with PolymarketClient(settings) as client:
        while datetime.now(UTC) < stop_at:
            try:
                # Update Binance price
                binance_price = await detector.update_price()
                price_change = detector.price_tracker.get_price_change()

                # Get Polymarket orderbooks
                up_book, down_book = await get_orderbook_state(client, market)

                up_bid, up_ask = extract_best_prices(up_book)
                down_bid, down_ask = extract_best_prices(down_book)

                # Calculate spread
                spread = Decimal("0")
                if up_ask and down_ask:
                    spread = up_ask + down_ask - Decimal("1")

                # Check for latency arbitrage signal
                signal = None
                if up_book:
                    snapshot = normalize_orderbook(
                        up_book, received_at=datetime.now(UTC)
                    )
                    signal = detector.detect_signal(
                        snapshot=snapshot,
                        market_id=market.condition_id,
                        up_asset_id=market.up_token_id,
                        down_asset_id=market.down_token_id,
                    )

                # Check for pair cost arbitrage (YES + NO < $1)
                pair_arb = calculate_pair_arbitrage(
                    up_ask=up_ask,
                    down_ask=down_ask,
                    market_id=market.condition_id,
                    up_asset_id=market.up_token_id,
                    down_asset_id=market.down_token_id,
                )

                state = MarketState(
                    timestamp=datetime.now(UTC),
                    binance_price=binance_price.price,
                    binance_change_30s_pct=price_change.change_pct if price_change else Decimal("0"),
                    up_bid=up_bid,
                    up_ask=up_ask,
                    down_bid=down_bid,
                    down_ask=down_ask,
                    spread=spread,
                    signal=signal,
                    pair_arb_signal=pair_arb,
                )
                states.append(state)

                # Log to file
                state_dict = {
                    "timestamp": state.timestamp.isoformat(),
                    "binance_price": str(state.binance_price),
                    "binance_change_30s_pct": str(state.binance_change_30s_pct),
                    "up_bid": str(state.up_bid) if state.up_bid else None,
                    "up_ask": str(state.up_ask) if state.up_ask else None,
                    "down_bid": str(state.down_bid) if state.down_bid else None,
                    "down_ask": str(state.down_ask) if state.down_ask else None,
                    "spread": str(state.spread),
                    "signal": asdict(signal) if signal else None,
                    "pair_arb": asdict(pair_arb) if pair_arb else None,
                }

                with output_file.open("a") as f:
                    f.write(json.dumps(state_dict, default=str) + "\n")

                if db_conn:
                    await persist_market_state(db_conn, market, state)

                # Log signals
                if signal and signal.is_actionable:
                    logger.info(
                        "LATENCY_ARB_SIGNAL",
                        direction=signal.direction,
                        edge_pct=f"{float(signal.edge_pct):.2f}%",
                        binance_change=f"{float(signal.binance_change_pct):.3f}%",
                        fair_prob=f"{float(signal.fair_probability):.3f}",
                        market_prob=f"{float(signal.market_probability):.3f}",
                    )
                elif pair_arb and pair_arb.is_actionable:
                    logger.info(
                        "PAIR_ARB_SIGNAL",
                        up_ask=f"{float(pair_arb.up_ask):.3f}",
                        down_ask=f"{float(pair_arb.down_ask):.3f}",
                        total_cost=f"{float(pair_arb.total_cost):.3f}",
                        net_profit_pct=f"{float(pair_arb.net_profit_pct):.2f}%",
                    )
                else:
                    # Regular status update every 5 seconds
                    if len(states) % 10 == 0:
                        logger.info(
                            "market_tick",
                            btc=f"${float(binance_price.price):,.2f}",
                            change_30s=f"{float(price_change.change_pct):.3f}%" if price_change else "N/A",
                            up_ask=f"{float(up_ask):.3f}" if up_ask else "N/A",
                            spread=f"{float(spread):.3f}",
                        )

            except Exception as e:
                logger.warning("monitor_tick_error", error=str(e))

            await asyncio.sleep(interval_ms / 1000)

    latency_signals = sum(1 for s in states if s.signal and s.signal.is_actionable)
    pair_arb_signals = sum(1 for s in states if s.pair_arb_signal and s.pair_arb_signal.is_actionable)

    logger.info(
        "monitoring_completed",
        market=market.title,
        ticks_recorded=len(states),
        latency_arb_signals=latency_signals,
        pair_arb_signals=pair_arb_signals,
        output_file=str(output_file),
    )

    return states


async def run_continuous_monitoring(
    settings,
    output_dir: Path,
    max_markets: int = 10,
    interval_ms: int = 500,
    db_conn: asyncpg.Connection | None = None,
    max_seconds: int | None = None,
):
    """Continuously monitor BTC 5-min markets."""
    markets_monitored = 0

    while markets_monitored < max_markets:
        # Find current/next market
        market = await find_current_btc_5min_market(settings)

        if not market:
            logger.info("waiting_for_market", sleep_seconds=10)
            await asyncio.sleep(10)
            continue

        # Check if market has already started
        now = datetime.now(UTC)
        if now < market.start_time:
            wait_seconds = (market.start_time - now).total_seconds()
            if wait_seconds > 0:
                logger.info(
                    "waiting_for_market_start",
                    market=market.title,
                    seconds=wait_seconds,
                )
                await asyncio.sleep(min(wait_seconds, 30))
                continue

        # Monitor this market
        await monitor_market(market, settings, output_dir, interval_ms, db_conn, max_seconds)
        markets_monitored += 1

        # Brief pause before finding next market
        await asyncio.sleep(2)


async def run() -> int:
    parser = argparse.ArgumentParser(
        description="Monitor BTC 5-min markets for latency arbitrage"
    )
    parser.add_argument(
        "--markets",
        type=int,
        default=3,
        help="Number of markets to monitor",
    )
    parser.add_argument(
        "--interval-ms",
        type=int,
        default=500,
        help="Milliseconds between price checks",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("logs/btc-5min-monitor"),
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Monitor only the current market then exit",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Disable Postgres persistence and only write JSONL logs.",
    )
    parser.add_argument(
        "--max-seconds",
        type=int,
        default=None,
        help="Optional cap for each monitored market, useful for smoke tests.",
    )
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)

    logger.info(
        "btc_5min_monitor_started",
        max_markets=args.markets,
        interval_ms=args.interval_ms,
    )

    db_conn = None
    if not args.no_db:
        db_conn = await asyncpg.connect(resolve_database_url(settings.database_url))
        await ensure_monitor_table(db_conn)

    try:
        if args.single:
            market = await find_current_btc_5min_market(settings)
            if market:
                await monitor_market(
                    market, settings, args.output_dir, args.interval_ms, db_conn, args.max_seconds
                )
            else:
                logger.error("no_active_market_found")
                return 1
        else:
            await run_continuous_monitoring(
                settings,
                args.output_dir,
                args.markets,
                args.interval_ms,
                db_conn,
                args.max_seconds,
            )
    finally:
        if db_conn:
            await db_conn.close()

    return 0


async def ensure_monitor_table(conn: asyncpg.Connection) -> None:
    await conn.execute(CREATE_MONITOR_TABLE_SQL)


async def persist_market_state(
    conn: asyncpg.Connection,
    market: MarketInfo,
    state: MarketState,
) -> None:
    pair_cost = None
    if state.up_ask is not None and state.down_ask is not None:
        pair_cost = state.up_ask + state.down_ask
    market_state, rejected_reason = classify_market_state(state, pair_cost)
    await conn.execute(
        """
        INSERT INTO app.btc_5m_monitor_ticks (
            observed_at, condition_id, market_slug, market_title, market_start, market_end,
            up_asset_id, down_asset_id, binance_price, binance_change_30s_pct,
            up_bid, up_ask, down_bid, down_ask, pair_cost, spread,
            market_state, rejected_reason, latency_signal, pair_arb_signal,
            has_latency_signal, has_pair_arb_signal
        )
        VALUES (
            $1, $2, $3, $4, $5, $6,
            $7, $8, $9, $10,
            $11, $12, $13, $14, $15, $16,
            $17, $18, $19::jsonb, $20::jsonb,
            $21, $22
        )
        """,
        state.timestamp,
        market.condition_id,
        market.slug,
        market.title,
        market.start_time,
        market.end_time,
        market.up_token_id,
        market.down_token_id,
        state.binance_price,
        state.binance_change_30s_pct,
        state.up_bid,
        state.up_ask,
        state.down_bid,
        state.down_ask,
        pair_cost,
        state.spread,
        market_state,
        rejected_reason,
        json.dumps(asdict(state.signal), default=str) if state.signal else None,
        json.dumps(asdict(state.pair_arb_signal), default=str) if state.pair_arb_signal else None,
        bool(state.signal and state.signal.is_actionable),
        bool(state.pair_arb_signal and state.pair_arb_signal.is_actionable),
    )


def classify_market_state(state: MarketState, pair_cost: Decimal | None) -> tuple[str, str]:
    if state.signal and state.signal.is_actionable:
        return "SIGNAL", "latency arbitrage signal detected"
    if state.pair_arb_signal and state.pair_arb_signal.is_actionable:
        return "SIGNAL", "pair cost arbitrage signal detected"
    if state.up_ask is None or state.down_ask is None:
        return "NO_BOOK", "missing one or both asks"
    if pair_cost is not None and pair_cost < Decimal("1"):
        return "SIGNAL", "YES + NO ask cost below 1"
    if state.spread >= Decimal("0.20"):
        return "ILLIQUID", "spread >= 20%"
    if state.spread >= Decimal("0.10"):
        return "WATCH", "spread between 10% and 20%"
    if abs(state.binance_change_30s_pct) < Decimal("0.30"):
        return "TRADEABLE", "spread acceptable but BTC 30s move below 0.30%"
    return "WATCH", "BTC move threshold met but edge detector did not confirm"


def normalize_database_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


def resolve_database_url(settings_url: str) -> str:
    url = os.getenv("DATABASE_URL", settings_url)
    normalized = normalize_database_url(url)
    if "@localhost:" in normalized:
        normalized = normalized.replace("@localhost:", "@postgres:", 1)
    if "@127.0.0.1:" in normalized:
        normalized = normalized.replace("@127.0.0.1:", "@postgres:", 1)
    return normalized


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
