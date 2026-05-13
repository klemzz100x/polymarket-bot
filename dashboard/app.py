from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from html import escape
import os
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

import asyncpg
import streamlit as st
import streamlit.components.v1 as components

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None


st.set_page_config(page_title="Polybot Trading Validation Dashboard", layout="wide")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://polymarket:change-me@postgres:5432/polymarket",
)
API_HEALTH_URL = os.getenv("POLYBOT_API_HEALTH_URL", "http://api:8000/health")
RESOURCES_DIR = Path(os.getenv("RESOURCES_DIR", "/app/resources"))
OBSIDIAN_VAULT_DIR = Path(os.getenv("OBSIDIAN_VAULT_DIR", "/app/obsidian-vault"))
AUTO_REFRESH_OPTIONS = {
    "Off": 0,
    "5 sec": 5,
    "15 sec": 15,
    "30 sec": 30,
    "60 sec": 60,
}
TWITTER_URL_RE = re.compile(r"https?://(?:x\.com|twitter\.com)/[^\s<>()]+", re.IGNORECASE)


def main() -> None:
    st.title("Polybot Trading Validation Dashboard")
    st.caption("Read-only dashboard for paper trading, shadow trading, readiness, and system health.")
    st.warning("Read-only mode: no order placement, no DB edits, no live trading controls.")

    page = st.sidebar.radio(
        "Page",
        [
            "Terminal Cockpit",
            "Overview",
            "Data Coverage",
            "Equity Curve",
            "Strategy Performance",
            "Market Performance",
            "Signals",
            "Risk",
            "System Health",
            "Shadow Trading",
            "Live Readiness",
            "Execution Quality",
            "Wallet",
            "OMS",
            "Twitter Research",
        ],
    )
    if page == "Terminal Cockpit":
        terminal_cockpit_page()
    elif page == "Overview":
        overview_page()
    elif page == "Data Coverage":
        data_coverage_page()
    elif page == "Equity Curve":
        equity_curve_page()
    elif page == "Strategy Performance":
        strategy_performance_page()
    elif page == "Market Performance":
        market_performance_page()
    elif page == "Signals":
        signals_page()
    elif page == "Risk":
        risk_page()
    elif page == "System Health":
        system_health_page()
    elif page == "Shadow Trading":
        shadow_trading_page()
    elif page == "Live Readiness":
        live_readiness_page()
    elif page == "Execution Quality":
        execution_quality_page()
    elif page == "Wallet":
        wallet_page()
    elif page == "OMS":
        oms_page()
    else:
        twitter_research_page()


def terminal_cockpit_page() -> None:
    inject_terminal_css()
    refresh_label = st.sidebar.selectbox("Auto-refresh", list(AUTO_REFRESH_OPTIONS), index=2)
    maybe_auto_refresh(AUTO_REFRESH_OPTIONS[refresh_label])

    summary = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM app.markets) AS markets,
            (SELECT COUNT(DISTINCT condition_id) FROM app.orderbook_snapshots) AS covered_markets,
            (SELECT COUNT(DISTINCT asset_id) FROM app.orderbook_snapshots) AS covered_assets,
            (SELECT COUNT(*) FROM app.orderbook_snapshots) AS snapshots,
            (SELECT MAX(snapshot_ts) FROM app.orderbook_snapshots) AS latest_snapshot_ts,
            (SELECT COALESCE(SUM(net_pnl), 0) FROM app.paper_trading_runs) AS net_pnl,
            (SELECT COALESCE(SUM(attempted_orders), 0) FROM app.paper_trading_runs) AS paper_orders,
            (SELECT COALESCE(SUM(filled_orders), 0) FROM app.paper_trading_runs) AS paper_fills,
            (SELECT COALESCE(SUM(rejected_orders), 0) FROM app.paper_trading_runs) AS rejected_orders,
            (SELECT COALESCE(SUM(decision_count), 0) FROM app.shadow_trading_runs) AS shadow_decisions,
            (SELECT COALESCE(SUM(theoretical_fill_count), 0) FROM app.shadow_trading_runs) AS shadow_fills,
            (SELECT COALESCE(SUM(missed_fill_count), 0) FROM app.shadow_trading_runs) AS shadow_missed,
            (SELECT COUNT(*) FROM app.ingestion_logs WHERE status <> 'success' AND started_at > now() - interval '24 hours') AS ingestion_errors_24h
        """
    )
    readiness = fetch_one(
        """
        SELECT status, live_readiness_score, execution_quality_score,
               infrastructure_health_score, strategy_stability_score,
               kill_switch_state, generated_at
        FROM app.live_readiness_reports
        ORDER BY generated_at DESC
        LIMIT 1
        """
    )
    equity = fetch_one(
        """
        SELECT snapshot_ts, strategy_name, market_id, equity, net_pnl, exposure
        FROM app.paper_equity_snapshots
        ORDER BY snapshot_ts DESC
        LIMIT 1
        """
    )

    st.markdown("### Terminal Cockpit")
    st.caption("Dense read-only view. All widgets refresh from Postgres/API; no order placement or live controls.")

    status_cols = st.columns(6)
    status_cols[0].metric("API", api_health())
    status_cols[1].metric("Markets", fmt_compact(summary.get("covered_markets")), delta=f"{fmt_compact(summary.get('covered_assets'))} books")
    status_cols[2].metric("Snapshots", fmt_compact(summary.get("snapshots")), delta=age_label(summary.get("latest_snapshot_ts")))
    status_cols[3].metric("Readiness", fmt_compact(readiness.get("status")), delta=fmt_compact(readiness.get("live_readiness_score")))
    status_cols[4].metric("Kill switch", fmt_compact(readiness.get("kill_switch_state")))
    status_cols[5].metric("Live mode", os.getenv("LIVE_EXECUTION_MODE", "DISABLED"))

    pnl_cols = st.columns(6)
    pnl_cols[0].metric("Equity", fmt_money(equity.get("equity")))
    pnl_cols[1].metric("Net PnL", fmt_money(summary.get("net_pnl")))
    pnl_cols[2].metric("Exposure", fmt_money(equity.get("exposure")))
    pnl_cols[3].metric("Paper fills", fmt_compact(summary.get("paper_fills")), delta=f"{fmt_compact(summary.get('paper_orders'))} orders")
    pnl_cols[4].metric("Shadow fills", fmt_compact(summary.get("shadow_fills")), delta=f"{fmt_compact(summary.get('shadow_missed'))} missed")
    pnl_cols[5].metric("Ingestion errors 24h", fmt_compact(summary.get("ingestion_errors_24h")))

    left, center, right = st.columns([1.15, 1.8, 1.15])
    with left:
        render_compact_table("Latest validation runs", fetch_all(_latest_runs_query())[:10], height=240)
        render_orderbook_depth(fetch_all(_orderbook_pressure_query(limit=8)))
    with center:
        render_equity_panel()
        render_compact_table("Freshest markets", fetch_all(_market_coverage_query(limit=12)), height=255)
    with right:
        render_signal_tape(fetch_all(_recent_signals_query(limit=12)))
        render_runtime_console(fetch_all(_runtime_console_query(limit=24)))

    bottom_left, bottom_right = st.columns([1.2, 1.0])
    with bottom_left:
        render_compact_table("Recent shadow decisions", fetch_all(_recent_shadow_decisions_query(limit=18)), height=260)
    with bottom_right:
        render_readiness_panel(readiness)


def twitter_research_page() -> None:
    st.subheader("Twitter Research Inbox")
    st.caption(
        "Paste X/Twitter thread URLs or raw notes. The dashboard writes a raw inbox file "
        "and clean Markdown source notes for the Obsidian research layer."
    )
    st.info("Research-only workflow: no trading controls, no DB mutation, no live execution.")

    title = st.text_input("Batch title", value=f"Twitter Research {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
    raw_input = st.text_area(
        "Thread URLs / raw notes",
        height=220,
        placeholder="https://x.com/user/status/123...\nhttps://x.com/another/status/456...\n\nOptional notes or context...",
    )
    col1, col2 = st.columns([1, 3])
    with col1:
        create_clicked = st.button("Add to research vault", type="primary")
    with col2:
        st.caption(f"Resources: `{RESOURCES_DIR}` | Vault: `{OBSIDIAN_VAULT_DIR}`")

    if create_clicked:
        try:
            result = create_twitter_research_batch(raw_input, title)
        except ValueError as exc:
            st.error(str(exc))
            return
        st.success(f"Research batch created: {result['batch_id']}")
        st.write("Raw inbox file:", str(result["raw_path"]))
        st.write("Research index note:", str(result["index_note_path"]))
        st.dataframe(to_frame(result["notes"]), use_container_width=True)

    st.subheader("Recent Twitter Source Notes")
    source_dir = OBSIDIAN_VAULT_DIR / "Sources" / "Twitter-Threads"
    notes = list_recent_markdown_notes(source_dir, limit=25)
    st.dataframe(to_frame(notes), use_container_width=True)


def inject_terminal_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(118, 255, 189, 0.16);
            border-radius: 6px;
            padding: 0.65rem 0.75rem;
            background: rgba(0, 0, 0, 0.22);
        }
        .terminal-line {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.82rem;
            border-bottom: 1px solid rgba(255,255,255,0.06);
            padding: 0.28rem 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .terminal-good { color: #5df2a0; }
        .terminal-warn { color: #ffb84d; }
        .terminal-bad { color: #ff6b6b; }
        .terminal-muted { color: rgba(255,255,255,0.56); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def maybe_auto_refresh(seconds: int) -> None:
    if seconds <= 0:
        return
    components.html(
        f"""
        <script>
        setTimeout(function() {{
            window.parent.location.reload();
        }}, {seconds * 1000});
        </script>
        """,
        height=0,
    )


def render_compact_table(title: str, rows: list[dict[str, Any]], *, height: int) -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        frame = to_frame(rows)
        if pd is not None and frame.empty:
            st.caption("empty")
        else:
            st.dataframe(frame, use_container_width=True, height=height)


def render_equity_panel() -> None:
    rows = fetch_all(
        """
        SELECT snapshot_ts, strategy_name, equity, net_pnl, exposure
        FROM app.paper_equity_snapshots
        ORDER BY snapshot_ts DESC
        LIMIT 500
        """
    )
    with st.container(border=True):
        st.markdown("**Equity / PnL**")
        frame = to_frame(list(reversed(rows)))
        if pd is not None and not frame.empty:
            chart_cols = [col for col in ["equity", "net_pnl"] if col in frame.columns]
            st.line_chart(frame, x="snapshot_ts", y=chart_cols, height=260)
        else:
            st.caption("empty")


def render_orderbook_depth(rows: list[dict[str, Any]]) -> None:
    with st.container(border=True):
        st.markdown("**Orderbook pressure**")
        if not rows:
            st.caption("empty")
            return
        for row in rows:
            pressure = row.get("bid_pressure")
            pressure_float = float(pressure) if pressure is not None else 0.0
            label = row.get("question") or row.get("market_id") or "market"
            spread = fmt_compact(row.get("spread"))
            st.caption(f"{str(label)[:58]} | spread {spread}")
            st.progress(max(0.0, min(1.0, pressure_float)))


def render_signal_tape(rows: list[dict[str, Any]]) -> None:
    with st.container(border=True):
        st.markdown("**Signal tape**")
        if not rows:
            st.caption("empty")
            return
        for row in rows:
            severity = str(row.get("severity") or "").lower()
            css_class = "terminal-good"
            if severity in {"high", "critical"}:
                css_class = "terminal-bad"
            elif severity in {"medium", "warning"}:
                css_class = "terminal-warn"
            text = (
                f"{fmt_time(row.get('event_ts'))} "
                f"{row.get('signal_type') or 'signal'} "
                f"conf={fmt_compact(row.get('confidence'))} "
                f"{row.get('description') or ''}"
            )
            st.markdown(
                f"<div class='terminal-line {css_class}'>{escape(text)}</div>",
                unsafe_allow_html=True,
            )


def render_runtime_console(rows: list[dict[str, Any]]) -> None:
    with st.container(border=True):
        st.markdown("**Runtime console**")
        if not rows:
            st.caption("empty")
            return
        for row in rows:
            severity = str(row.get("severity") or "info")
            css_class = "terminal-muted" if severity == "info" else "terminal-warn"
            text = f"{fmt_time(row.get('event_ts'))} {row.get('line') or ''}"
            st.markdown(
                f"<div class='terminal-line {css_class}'>{escape(text)}</div>",
                unsafe_allow_html=True,
            )


def render_readiness_panel(latest: dict[str, Any]) -> None:
    with st.container(border=True):
        st.markdown("**Live readiness guardrails**")
        st.metric("Readiness score", fmt_compact(latest.get("live_readiness_score")))
        st.metric("Execution quality", fmt_compact(latest.get("execution_quality_score")))
        st.metric("Infrastructure health", fmt_compact(latest.get("infrastructure_health_score")))
        st.metric("Strategy stability", fmt_compact(latest.get("strategy_stability_score")))
        st.caption(f"Generated: {fmt(latest.get('generated_at'))}")


def create_twitter_research_batch(raw_input: str, title: str) -> dict[str, Any]:
    raw = raw_input.strip()
    if not raw:
        raise ValueError("Paste at least one Twitter/X URL or raw research note.")

    batch_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    resources_dir = RESOURCES_DIR / "twitter-threads"
    source_dir = OBSIDIAN_VAULT_DIR / "Sources" / "Twitter-Threads"
    research_dir = OBSIDIAN_VAULT_DIR / "Research" / "Twitter-Inbox"
    resources_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)
    research_dir.mkdir(parents=True, exist_ok=True)

    raw_path = resources_dir / f"dashboard-inbox-{batch_id}.txt"
    raw_path.write_text(raw + "\n", encoding="utf-8")

    urls = extract_twitter_urls(raw)
    if not urls:
        urls = [f"raw-note://dashboard/{batch_id}"]

    notes: list[dict[str, Any]] = []
    for index, url in enumerate(urls, start=1):
        parsed = parse_twitter_url(url)
        note_slug = parsed["slug"] if parsed["status_id"] != "raw" else f"raw-note-{batch_id}-{index}"
        note_path = source_dir / f"{note_slug}.md"
        note_path.write_text(
            render_twitter_research_note(
                title=title,
                batch_id=batch_id,
                url=parsed["clean_url"],
                author=parsed["author"],
                status_id=parsed["status_id"],
                raw_context=raw,
            ),
            encoding="utf-8",
        )
        notes.append(
            {
                "source": parsed["clean_url"],
                "author": parsed["author"],
                "status_id": parsed["status_id"],
                "note_path": str(note_path),
            }
        )

    index_note_path = research_dir / f"twitter-research-inbox-{batch_id}.md"
    index_note_path.write_text(
        render_twitter_research_index(title=title, batch_id=batch_id, raw_path=raw_path, notes=notes),
        encoding="utf-8",
    )
    return {
        "batch_id": batch_id,
        "raw_path": raw_path,
        "index_note_path": index_note_path,
        "notes": notes,
    }


def extract_twitter_urls(text: str) -> list[str]:
    urls: list[str] = []
    for match in TWITTER_URL_RE.findall(text):
        clean = match.rstrip(".,;]")
        if clean not in urls:
            urls.append(clean)
    return urls


def parse_twitter_url(url: str) -> dict[str, str]:
    if url.startswith("raw-note://"):
        return {
            "clean_url": url,
            "author": "raw-note",
            "status_id": "raw",
            "slug": slugify(url),
        }
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    author = parts[0] if parts else "unknown"
    status_id = "unknown"
    if len(parts) >= 3 and parts[1] in {"status", "statuses"}:
        status_id = parts[2]
    clean_url = f"https://x.com/{author}/status/{status_id}" if status_id != "unknown" else url.split("?")[0]
    return {
        "clean_url": clean_url,
        "author": author,
        "status_id": status_id,
        "slug": slugify(f"{author}-{status_id}"),
    }


def render_twitter_research_note(
    *,
    title: str,
    batch_id: str,
    url: str,
    author: str,
    status_id: str,
    raw_context: str,
) -> str:
    raw_excerpt = raw_context[:2500]
    return f"""# Twitter Thread Research - @{author} - {status_id}

## Source
{url}

## Capture
- Batch: {batch_id}
- Dashboard title: {title}
- Status: inboxed for research mining

## Raw Context
```text
{raw_excerpt}
```

## Research Tasks
- Extract actionable strategy ideas.
- Classify possible edge families.
- Link each idea to measurable signals.
- Identify required Polymarket data.
- Decide whether this can become a Strategy Candidate.

## Edge Families To Check
- spread capture
- market making
- orderbook imbalance
- liquidity vacuum
- stale orderbook
- delayed repricing
- cross-market arbitrage
- news latency
- event-driven repricing
- behavioral overreaction
- resolution edge

## Strategy Candidate Hooks
- Hypothesis:
- Required data:
- Testable signal:
- Backtest design:
- Main risk:
- Priority:

## Links
[[Strategy Candidates]]
[[Obsidian Strategy Mining]]
[[Data Layer]]
[[Backtesting]]
[[Paper Trading]]
"""


def render_twitter_research_index(
    *, title: str, batch_id: str, raw_path: Path, notes: list[dict[str, Any]]
) -> str:
    links = "\n".join(f"- [{note['source']}]({note['source']}) -> `{note['note_path']}`" for note in notes)
    return f"""# {title}

## Metadata
- Batch: {batch_id}
- Raw inbox file: `{raw_path}`
- Created at: {datetime.now(UTC).isoformat()}

## Sources
{links}

## Research Objective
Turn these Twitter/X threads into testable Polymarket strategy candidates.

## Next Actions
- Run Obsidian strategy mining.
- Promote promising hypotheses to Strategy Candidates.
- Link candidates to backtests and paper/shadow trading results.

## Links
[[Strategy Candidates]]
[[Obsidian Strategy Mining]]
[[Research]]
[[Market Microstructure]]
"""


def list_recent_markdown_notes(directory: Path, *, limit: int) -> list[dict[str, Any]]:
    if not directory.exists():
        return []
    notes = sorted(directory.glob("*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    return [
        {
            "note": path.stem,
            "path": str(path),
            "updated_at": datetime.fromtimestamp(path.stat().st_mtime, tz=UTC),
        }
        for path in notes[:limit]
    ]


def overview_page() -> None:
    data = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM app.markets) AS markets,
            (SELECT COUNT(*) FROM app.market_outcomes WHERE asset_id IS NOT NULL) AS outcomes,
            (SELECT COUNT(*) FROM app.orderbook_snapshots) AS snapshots,
            (SELECT COUNT(DISTINCT condition_id) FROM app.orderbook_snapshots) AS covered_markets,
            (SELECT COUNT(DISTINCT asset_id) FROM app.orderbook_snapshots) AS covered_assets,
            (SELECT MAX(snapshot_ts) FROM app.orderbook_snapshots) AS latest_snapshot_ts,
            (SELECT COUNT(*) FROM app.paper_trading_runs) AS paper_runs,
            (SELECT COALESCE(SUM(signal_count), 0) FROM app.paper_trading_runs) AS paper_signals,
            (SELECT COALESCE(SUM(attempted_orders), 0) FROM app.paper_trading_runs) AS paper_orders,
            (SELECT COALESCE(SUM(filled_orders), 0) FROM app.paper_trading_runs) AS paper_fills,
            (SELECT COUNT(*) FROM app.shadow_trading_runs) AS shadow_runs,
            (SELECT COALESCE(SUM(decision_count), 0) FROM app.shadow_trading_runs) AS shadow_decisions,
            (SELECT COALESCE(SUM(missed_fill_count), 0) FROM app.shadow_trading_runs) AS shadow_missed,
            (SELECT COALESCE(SUM(theoretical_fill_count), 0) FROM app.shadow_trading_runs) AS shadow_fills
        """
    )
    readiness = fetch_one(
        """
        SELECT status, live_readiness_score, kill_switch_state, generated_at
        FROM app.live_readiness_reports
        ORDER BY generated_at DESC
        LIMIT 1
        """
    )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Markets", fmt(data.get("markets")))
    col2.metric("Covered markets", fmt(data.get("covered_markets")))
    col3.metric("Snapshots", fmt(data.get("snapshots")))
    col4.metric("Latest snapshot", fmt(data.get("latest_snapshot_ts")))

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Paper signals", fmt(data.get("paper_signals")))
    col6.metric("Paper orders", fmt(data.get("paper_orders")))
    col7.metric("Paper fills", fmt(data.get("paper_fills")))
    col8.metric("Shadow decisions", fmt(data.get("shadow_decisions")))

    col9, col10, col11, col12 = st.columns(4)
    col9.metric("Shadow fills", fmt(data.get("shadow_fills")))
    col10.metric("Shadow missed", fmt(data.get("shadow_missed")))
    col11.metric("Readiness", fmt(readiness.get("status")))
    col12.metric("Kill switch", fmt(readiness.get("kill_switch_state")))

    st.subheader("Latest Validation Runs")
    st.dataframe(to_frame(fetch_all(_latest_runs_query())))

    st.subheader("Freshest Market Data")
    st.dataframe(to_frame(fetch_all(_market_coverage_query(limit=20))))

    st.subheader("Recent Signals")
    st.dataframe(to_frame(fetch_all(_recent_signals_query(limit=50))))


def data_coverage_page() -> None:
    coverage = fetch_all(_market_coverage_query(limit=200))
    st.subheader("Market Data Coverage")
    st.dataframe(to_frame(coverage))

    freshness = fetch_one(
        """
        WITH latest AS (
            SELECT DISTINCT ON (condition_id, asset_id)
                condition_id, asset_id, snapshot_ts
            FROM app.orderbook_snapshots
            ORDER BY condition_id, asset_id, snapshot_ts DESC
        )
        SELECT
            COUNT(*) AS tracked_books,
            COUNT(*) FILTER (WHERE now() - snapshot_ts <= interval '60 seconds') AS fresh_books,
            COUNT(*) FILTER (WHERE now() - snapshot_ts > interval '60 seconds') AS stale_books,
            MAX(snapshot_ts) AS newest_snapshot,
            MIN(snapshot_ts) AS oldest_latest_snapshot
        FROM latest
        """
    )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tracked books", fmt(freshness.get("tracked_books")))
    col2.metric("Fresh books", fmt(freshness.get("fresh_books")))
    col3.metric("Stale books", fmt(freshness.get("stale_books")))
    col4.metric("Newest snapshot", fmt(freshness.get("newest_snapshot")))

    logs = fetch_all(
        """
        SELECT source, job_type, status, started_at, finished_at, rows_seen, rows_written, error_message
        FROM app.ingestion_logs
        ORDER BY started_at DESC
        LIMIT 200
        """
    )
    st.subheader("Ingestion Runs")
    st.dataframe(to_frame(logs))

    books = fetch_all(
        """
        SELECT s.condition_id AS market_id, s.asset_id, s.snapshot_ts,
               COUNT(l.id) AS levels,
               MAX(CASE WHEN l.side = 'bid' THEN l.price END) AS best_bid,
               MIN(CASE WHEN l.side = 'ask' THEN l.price END) AS best_ask,
               SUM(CASE WHEN l.side = 'bid' THEN l.size ELSE 0 END) AS bid_depth,
               SUM(CASE WHEN l.side = 'ask' THEN l.size ELSE 0 END) AS ask_depth
        FROM app.orderbook_snapshots s
        JOIN app.orderbook_levels l ON l.snapshot_id = s.id
        GROUP BY s.condition_id, s.asset_id, s.snapshot_ts
        ORDER BY s.snapshot_ts DESC
        LIMIT 200
        """
    )
    st.subheader("Latest Orderbooks")
    st.dataframe(to_frame(books))


def equity_curve_page() -> None:
    rows = fetch_all(
        """
        SELECT snapshot_ts, strategy_name, market_id, equity, net_pnl, exposure
        FROM app.paper_equity_snapshots
        ORDER BY snapshot_ts ASC
        LIMIT 5000
        """
    )
    frame = to_frame(rows)
    st.subheader("Equity Curve")
    if pd is not None and not frame.empty:
        st.line_chart(frame, x="snapshot_ts", y="equity", color="strategy_name")
        st.line_chart(frame, x="snapshot_ts", y="net_pnl", color="strategy_name")
    else:
        st.dataframe(frame)

    st.subheader("Drawdown Approximation")
    drawdown_rows = fetch_all(
        """
        WITH ordered AS (
            SELECT snapshot_ts, strategy_name, equity,
                   MAX(equity) OVER (PARTITION BY strategy_name ORDER BY snapshot_ts) AS peak
            FROM app.paper_equity_snapshots
        )
        SELECT snapshot_ts, strategy_name,
               CASE WHEN peak > 0 THEN (peak - equity) / peak ELSE 0 END AS drawdown
        FROM ordered
        ORDER BY snapshot_ts ASC
        LIMIT 5000
        """
    )
    drawdown = to_frame(drawdown_rows)
    if pd is not None and not drawdown.empty:
        st.line_chart(drawdown, x="snapshot_ts", y="drawdown", color="strategy_name")
    else:
        st.dataframe(drawdown)


def strategy_performance_page() -> None:
    rows = fetch_all(
        """
        SELECT
            strategy_name,
            COUNT(*) AS runs,
            COALESCE(SUM(net_pnl), 0) AS net_pnl,
            COALESCE(SUM(fees), 0) AS fees,
            COALESCE(SUM(filled_orders), 0) AS filled_orders,
            COALESCE(SUM(rejected_orders), 0) AS rejected_orders,
            CASE WHEN COALESCE(SUM(attempted_orders), 0) > 0
                THEN SUM(filled_orders)::numeric / SUM(attempted_orders)
                ELSE 0
            END AS fill_rate
        FROM app.paper_trading_runs
        GROUP BY strategy_name
        ORDER BY net_pnl DESC
        """
    )
    st.subheader("Strategy Ranking")
    st.dataframe(to_frame(rows))


def market_performance_page() -> None:
    rows = fetch_all(
        """
        SELECT
            market_id,
            COUNT(*) AS runs,
            COALESCE(SUM(net_pnl), 0) AS net_pnl,
            COALESCE(SUM(filled_orders), 0) AS filled_orders,
            COALESCE(SUM(rejected_orders), 0) AS rejected_orders
        FROM app.paper_trading_runs
        GROUP BY market_id
        ORDER BY net_pnl DESC
        """
    )
    st.subheader("Market Performance")
    st.dataframe(to_frame(rows))

    spreads = fetch_all(
        """
        WITH best_levels AS (
            SELECT s.condition_id, s.asset_id, s.snapshot_ts,
                   MAX(CASE WHEN l.side = 'bid' THEN l.price END) AS best_bid,
                   MIN(CASE WHEN l.side = 'ask' THEN l.price END) AS best_ask
            FROM app.orderbook_snapshots s
            JOIN app.orderbook_levels l ON l.snapshot_id = s.id
            GROUP BY s.condition_id, s.asset_id, s.snapshot_ts
        )
        SELECT condition_id AS market_id,
               AVG(best_ask - best_bid) AS average_spread,
               COUNT(*) AS snapshot_count
        FROM best_levels
        WHERE best_bid IS NOT NULL AND best_ask IS NOT NULL
        GROUP BY condition_id
        ORDER BY average_spread DESC
        LIMIT 50
        """
    )
    st.subheader("Average Spread by Market")
    st.dataframe(to_frame(spreads))


def signals_page() -> None:
    rows = fetch_all(
        _recent_signals_query(limit=200)
    )
    st.subheader("Latest Signals")
    st.dataframe(to_frame(rows))

    signal_counts = fetch_all(
        """
        SELECT payload->>'signal_type' AS signal_type,
               payload->>'severity' AS severity,
               COUNT(*) AS count,
               AVG((payload->>'confidence')::numeric) AS avg_confidence
        FROM app.paper_trading_events
        WHERE event_type = 'research_signal'
        GROUP BY payload->>'signal_type', payload->>'severity'
        ORDER BY count DESC
        """
    )
    st.subheader("Signal Counts")
    st.dataframe(to_frame(signal_counts))

    hit_rows = fetch_all(
        """
        SELECT
            r.strategy_name,
            COALESCE(SUM(r.signal_count), 0) AS signals,
            COALESCE(SUM(r.filled_orders), 0) AS fills,
            CASE WHEN COALESCE(SUM(r.signal_count), 0) > 0
                THEN SUM(r.filled_orders)::numeric / SUM(r.signal_count)
                ELSE 0
            END AS signal_hit_rate
        FROM app.paper_trading_runs r
        GROUP BY r.strategy_name
        ORDER BY signal_hit_rate DESC
        """
    )
    st.subheader("Signal Hit Rate")
    st.dataframe(to_frame(hit_rows))


def risk_page() -> None:
    exposure_rows = fetch_all(
        """
        SELECT strategy_name, market_id, snapshot_ts, exposure, positions
        FROM app.paper_equity_snapshots
        ORDER BY snapshot_ts DESC
        LIMIT 100
        """
    )
    st.subheader("Latest Exposure")
    st.dataframe(to_frame(exposure_rows))

    rejections = fetch_all(
        """
        SELECT event_ts, run_id, payload->>'reason' AS reason, payload
        FROM app.paper_trading_events
        WHERE event_type = 'paper_order_rejected'
        ORDER BY event_ts DESC
        LIMIT 100
        """
    )
    st.subheader("Rejected Orders")
    st.dataframe(to_frame(rejections))


def system_health_page() -> None:
    col1, col2 = st.columns(2)
    col1.metric("API health", api_health())
    db_ok = bool(fetch_one("SELECT 1 AS ok").get("ok"))
    col2.metric("DB health", "ok" if db_ok else "error")

    logs = fetch_all(
        """
        SELECT source, job_type, status, started_at, finished_at, rows_seen, rows_written, error_message
        FROM app.ingestion_logs
        ORDER BY started_at DESC
        LIMIT 100
        """
    )
    st.subheader("Collector Status")
    st.dataframe(to_frame(logs))

    stale = fetch_all(
        """
        WITH latest AS (
            SELECT DISTINCT ON (condition_id, asset_id)
                condition_id, asset_id, snapshot_ts, received_at
            FROM app.orderbook_snapshots
            ORDER BY condition_id, asset_id, snapshot_ts DESC
        )
        SELECT condition_id, asset_id, snapshot_ts,
               EXTRACT(EPOCH FROM (now() - snapshot_ts)) AS age_seconds
        FROM latest
        WHERE now() - snapshot_ts > interval '60 seconds'
        ORDER BY age_seconds DESC
        LIMIT 100
        """
    )
    st.subheader("Stale Markets")
    st.dataframe(to_frame(stale))


def shadow_trading_page() -> None:
    aggregate = fetch_one(
        """
        SELECT
            COUNT(*) AS runs,
            COALESCE(SUM(decision_count), 0) AS decisions,
            COALESCE(SUM(theoretical_fill_count), 0) AS theoretical_fills,
            COALESCE(SUM(missed_fill_count), 0) AS missed_fills,
            COALESCE(SUM(impossible_fill_count), 0) AS impossible_fills,
            AVG(average_slippage) AS average_slippage,
            AVG(fill_probability) AS fill_probability
        FROM app.shadow_trading_runs
        """
    )
    latest_run = fetch_one(
        """
        SELECT id, market_id, strategy_name, started_at, snapshot_count, signal_count,
               decision_count, theoretical_fill_count, missed_fill_count,
               impossible_fill_count, average_slippage, average_delay_ms, fill_probability
        FROM app.shadow_trading_runs
        ORDER BY started_at DESC
        LIMIT 1
        """
    )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Latest decisions", fmt(latest_run.get("decision_count")))
    col2.metric("Latest fills", fmt(latest_run.get("theoretical_fill_count")))
    col3.metric("Latest missed", fmt(latest_run.get("missed_fill_count")))
    col4.metric("Fill probability", fmt(latest_run.get("fill_probability")))

    col5, col6, col7 = st.columns(3)
    col5.metric("Total runs", fmt(aggregate.get("runs")))
    col6.metric("Total decisions", fmt(aggregate.get("decisions")))
    col7.metric("Total missed", fmt(aggregate.get("missed_fills")))

    runs = fetch_all(
        """
        SELECT id, market_id, strategy_name, started_at, finished_at, decision_count,
               theoretical_fill_count, missed_fill_count, impossible_fill_count,
               average_slippage, average_delay_ms, fill_probability
        FROM app.shadow_trading_runs
        ORDER BY started_at DESC
        LIMIT 100
        """
    )
    st.subheader("Latest Shadow Runs")
    st.dataframe(to_frame(runs))

    decisions = fetch_all(
        """
        SELECT decision_ts, market_id, asset_id, signal_type, action, status,
               fill_json->>'fill_possible' AS fill_possible,
               fill_json->>'filled_size' AS filled_size,
               fill_json->>'average_price' AS average_price,
               comparison_json->>'delay_ms' AS delay_ms,
               comparison_json->>'slippage_abs' AS slippage_abs
        FROM app.shadow_trading_decisions
        ORDER BY decision_ts DESC
        LIMIT 250
        """
    )
    st.subheader("Shadow Decisions")
    st.dataframe(to_frame(decisions))


def live_readiness_page() -> None:
    latest = fetch_one(
        """
        SELECT generated_at, status, live_readiness_score, execution_quality_score,
               infrastructure_health_score, strategy_stability_score, kill_switch_state
        FROM app.live_readiness_reports
        ORDER BY generated_at DESC
        LIMIT 1
        """
    )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Readiness status", fmt(latest.get("status")))
    col2.metric("Readiness score", fmt(latest.get("live_readiness_score")))
    col3.metric("Execution score", fmt(latest.get("execution_quality_score")))
    col4.metric("Kill switch", fmt(latest.get("kill_switch_state")))

    col5, col6, col7 = st.columns(3)
    col5.metric("Infrastructure score", fmt(latest.get("infrastructure_health_score")))
    col6.metric("Strategy score", fmt(latest.get("strategy_stability_score")))
    col7.metric("Live mode", os.getenv("LIVE_EXECUTION_MODE", "DISABLED"))

    reports = fetch_all(
        """
        SELECT generated_at, status, live_readiness_score, execution_quality_score,
               infrastructure_health_score, strategy_stability_score, kill_switch_state
        FROM app.live_readiness_reports
        ORDER BY generated_at DESC
        LIMIT 100
        """
    )
    st.subheader("Readiness Reports")
    st.dataframe(to_frame(reports))

    events = fetch_all(
        """
        SELECT event_ts, state, trigger, severity, reason, metadata
        FROM app.kill_switch_events
        ORDER BY event_ts DESC
        LIMIT 100
        """
    )
    st.subheader("Kill Switch Events")
    st.dataframe(to_frame(events))


def execution_quality_page() -> None:
    summary = fetch_one(
        """
        SELECT
            COALESCE(SUM(decision_count), 0) AS decisions,
            COALESCE(SUM(theoretical_fill_count), 0) AS fills,
            COALESCE(SUM(missed_fill_count), 0) AS missed,
            COALESCE(SUM(impossible_fill_count), 0) AS impossible,
            CASE WHEN COALESCE(SUM(decision_count), 0) > 0
                THEN SUM(theoretical_fill_count)::numeric / SUM(decision_count)
                ELSE 0
            END AS fill_ratio,
            CASE WHEN COALESCE(SUM(decision_count), 0) > 0
                THEN SUM(missed_fill_count)::numeric / SUM(decision_count)
                ELSE 0
            END AS missed_ratio
        FROM app.shadow_trading_runs
        """
    )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Shadow decisions", fmt(summary.get("decisions")))
    col2.metric("Fill ratio", fmt(summary.get("fill_ratio")))
    col3.metric("Missed ratio", fmt(summary.get("missed_ratio")))
    col4.metric("Impossible fills", fmt(summary.get("impossible")))

    quality = fetch_all(
        """
        SELECT strategy_name,
               COUNT(*) AS runs,
               AVG(average_slippage) AS average_slippage,
               AVG(average_delay_ms) AS average_delay_ms,
               AVG(fill_probability) AS fill_probability,
               SUM(missed_fill_count) AS missed_fills,
               SUM(impossible_fill_count) AS impossible_fills
        FROM app.shadow_trading_runs
        GROUP BY strategy_name
        ORDER BY average_slippage DESC
        """
    )
    st.subheader("Shadow Execution Quality")
    st.dataframe(to_frame(quality))

    spreads = fetch_all(
        """
        WITH best_levels AS (
            SELECT s.condition_id, s.asset_id, s.snapshot_ts,
                   MAX(CASE WHEN l.side = 'bid' THEN l.price END) AS best_bid,
                   MIN(CASE WHEN l.side = 'ask' THEN l.price END) AS best_ask,
                   SUM(CASE WHEN l.side = 'bid' THEN l.size ELSE 0 END) AS bid_depth,
                   SUM(CASE WHEN l.side = 'ask' THEN l.size ELSE 0 END) AS ask_depth
            FROM app.orderbook_snapshots s
            JOIN app.orderbook_levels l ON l.snapshot_id = s.id
            GROUP BY s.condition_id, s.asset_id, s.snapshot_ts
        )
        SELECT condition_id AS market_id, asset_id,
               AVG(best_ask - best_bid) AS average_spread,
               AVG(bid_depth) AS average_bid_depth,
               AVG(ask_depth) AS average_ask_depth,
               COUNT(*) AS snapshot_count
        FROM best_levels
        WHERE best_bid IS NOT NULL AND best_ask IS NOT NULL
        GROUP BY condition_id, asset_id
        ORDER BY average_spread DESC
        LIMIT 100
        """
    )
    st.subheader("Spread and Depth Conditions")
    st.dataframe(to_frame(spreads))

    stale = fetch_all(
        """
        WITH latest AS (
            SELECT DISTINCT ON (condition_id, asset_id)
                condition_id, asset_id, snapshot_ts
            FROM app.orderbook_snapshots
            ORDER BY condition_id, asset_id, snapshot_ts DESC
        )
        SELECT condition_id AS market_id, asset_id, snapshot_ts,
               EXTRACT(EPOCH FROM (now() - snapshot_ts)) AS age_seconds
        FROM latest
        WHERE now() - snapshot_ts > interval '60 seconds'
        ORDER BY age_seconds DESC
        LIMIT 100
        """
    )
    st.subheader("Stale Books")
    st.dataframe(to_frame(stale))

    live_quality = fetch_all(
        """
        SELECT status, accepted, reason, created_at, client_order_id, exchange_order_id
        FROM app.live_execution_reports
        ORDER BY created_at DESC
        LIMIT 100
        """
    )
    st.subheader("Live Execution Reports")
    st.dataframe(to_frame(live_quality))


def wallet_page() -> None:
    latest = fetch_one(
        """
        SELECT wallet_address, captured_at, total_exposure_usd, balances, positions, open_orders
        FROM app.wallet_snapshots
        ORDER BY captured_at DESC
        LIMIT 1
        """
    )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Wallet", fmt(latest.get("wallet_address")))
    col2.metric("Exposure", fmt(latest.get("total_exposure_usd")))
    col3.metric("Balances", fmt_len(latest.get("balances")))
    col4.metric("Open orders", fmt_len(latest.get("open_orders")))

    st.subheader("Balances")
    st.dataframe(to_frame(latest.get("balances") or []))
    st.subheader("Positions")
    st.dataframe(to_frame(latest.get("positions") or []))
    st.subheader("Open Orders")
    st.dataframe(to_frame(latest.get("open_orders") or []))

    history = fetch_all(
        """
        SELECT wallet_address, captured_at, total_exposure_usd
        FROM app.wallet_snapshots
        ORDER BY captured_at DESC
        LIMIT 100
        """
    )
    st.subheader("Wallet Sync History")
    st.dataframe(to_frame(history))


def oms_page() -> None:
    orders = fetch_all(
        """
        SELECT client_order_id, exchange_order_id, market_id, asset_id, strategy_name,
               side, price, size, notional_usd, mode, state, rejection_reason, updated_at
        FROM app.live_orders
        ORDER BY updated_at DESC
        LIMIT 200
        """
    )
    st.subheader("OMS Orders")
    st.dataframe(to_frame(orders))

    fills = fetch_all(
        """
        SELECT fill_id, exchange_order_id, client_order_id, market_id, asset_id,
               side, price, size, fee, filled_at
        FROM app.live_fills
        ORDER BY filled_at DESC
        LIMIT 200
        """
    )
    st.subheader("Fills")
    st.dataframe(to_frame(fills))

    risk_events = fetch_all(
        """
        SELECT event_ts, client_order_id, market_id, strategy_name, allowed, reason, checks
        FROM app.live_risk_events
        ORDER BY event_ts DESC
        LIMIT 200
        """
    )
    st.subheader("Risk Gate Events")
    st.dataframe(to_frame(risk_events))

    reconciliation = fetch_all(
        """
        SELECT generated_at, status, checked_orders, exchange_open_orders, report
        FROM app.oms_reconciliation_reports
        ORDER BY generated_at DESC
        LIMIT 100
        """
    )
    st.subheader("Reconciliation")
    st.dataframe(to_frame(reconciliation))


def _latest_runs_query() -> str:
    return """
        SELECT *
        FROM (
            SELECT
                'paper' AS layer,
                id,
                market_id,
                strategy_name,
                started_at,
                snapshot_count,
                signal_count,
                attempted_orders AS decisions,
                filled_orders AS fills,
                rejected_orders AS rejected_or_impossible,
                net_pnl::text AS pnl_or_slippage,
                result
            FROM app.paper_trading_runs
            UNION ALL
            SELECT
                'shadow' AS layer,
                id,
                market_id,
                strategy_name,
                started_at,
                snapshot_count,
                signal_count,
                decision_count AS decisions,
                theoretical_fill_count AS fills,
                impossible_fill_count AS rejected_or_impossible,
                average_slippage::text AS pnl_or_slippage,
                result
            FROM app.shadow_trading_runs
        ) runs
        ORDER BY started_at DESC
        LIMIT 50
    """


def _market_coverage_query(*, limit: int) -> str:
    return f"""
        WITH coverage AS (
            SELECT condition_id, asset_id,
                   COUNT(*) AS snapshot_count,
                   MIN(snapshot_ts) AS first_snapshot,
                   MAX(snapshot_ts) AS latest_snapshot
            FROM app.orderbook_snapshots
            GROUP BY condition_id, asset_id
        ),
        latest_books AS (
            SELECT DISTINCT ON (s.condition_id, s.asset_id)
                s.condition_id, s.asset_id, s.snapshot_ts,
                MAX(CASE WHEN l.side = 'bid' THEN l.price END) AS best_bid,
                MIN(CASE WHEN l.side = 'ask' THEN l.price END) AS best_ask,
                SUM(CASE WHEN l.side = 'bid' THEN l.size ELSE 0 END) AS bid_depth,
                SUM(CASE WHEN l.side = 'ask' THEN l.size ELSE 0 END) AS ask_depth
            FROM app.orderbook_snapshots s
            JOIN app.orderbook_levels l ON l.snapshot_id = s.id
            GROUP BY s.condition_id, s.asset_id, s.snapshot_ts
            ORDER BY s.condition_id, s.asset_id, s.snapshot_ts DESC
        )
        SELECT c.condition_id AS market_id,
               LEFT(COALESCE(m.question, ''), 120) AS question,
               c.asset_id,
               c.snapshot_count,
               c.first_snapshot,
               c.latest_snapshot,
               EXTRACT(EPOCH FROM (now() - c.latest_snapshot)) AS age_seconds,
               lb.best_bid,
               lb.best_ask,
               CASE
                    WHEN lb.best_bid IS NOT NULL AND lb.best_ask IS NOT NULL
                    THEN lb.best_ask - lb.best_bid
                    ELSE NULL
               END AS spread,
               lb.bid_depth,
               lb.ask_depth
        FROM coverage c
        LEFT JOIN app.markets m ON m.condition_id = c.condition_id
        LEFT JOIN latest_books lb ON lb.condition_id = c.condition_id AND lb.asset_id = c.asset_id
        ORDER BY c.latest_snapshot DESC
        LIMIT {limit}
    """


def _recent_signals_query(*, limit: int) -> str:
    return f"""
        SELECT event_ts,
               run_id,
               payload->>'market_id' AS market_id,
               payload->>'asset_id' AS asset_id,
               payload->>'signal_type' AS signal_type,
               payload->>'severity' AS severity,
               payload->>'confidence' AS confidence,
               payload->>'description' AS description,
               payload->>'hypothesis' AS hypothesis,
               payload->>'next_action' AS next_action
        FROM app.paper_trading_events
        WHERE event_type = 'research_signal'
        ORDER BY event_ts DESC
        LIMIT {limit}
    """


def _orderbook_pressure_query(*, limit: int) -> str:
    return f"""
        WITH latest_books AS (
            SELECT DISTINCT ON (s.condition_id, s.asset_id)
                s.condition_id,
                s.asset_id,
                s.snapshot_ts,
                MAX(CASE WHEN l.side = 'bid' THEN l.price END) AS best_bid,
                MIN(CASE WHEN l.side = 'ask' THEN l.price END) AS best_ask,
                SUM(CASE WHEN l.side = 'bid' THEN l.size ELSE 0 END) AS bid_depth,
                SUM(CASE WHEN l.side = 'ask' THEN l.size ELSE 0 END) AS ask_depth
            FROM app.orderbook_snapshots s
            JOIN app.orderbook_levels l ON l.snapshot_id = s.id
            GROUP BY s.condition_id, s.asset_id, s.snapshot_ts
            ORDER BY s.condition_id, s.asset_id, s.snapshot_ts DESC
        )
        SELECT lb.condition_id AS market_id,
               LEFT(COALESCE(m.question, lb.condition_id), 90) AS question,
               lb.asset_id,
               lb.snapshot_ts,
               lb.best_bid,
               lb.best_ask,
               CASE
                    WHEN lb.best_bid IS NOT NULL AND lb.best_ask IS NOT NULL
                    THEN lb.best_ask - lb.best_bid
                    ELSE NULL
               END AS spread,
               lb.bid_depth,
               lb.ask_depth,
               CASE
                    WHEN COALESCE(lb.bid_depth, 0) + COALESCE(lb.ask_depth, 0) > 0
                    THEN lb.bid_depth / (lb.bid_depth + lb.ask_depth)
                    ELSE NULL
               END AS bid_pressure
        FROM latest_books lb
        LEFT JOIN app.markets m ON m.condition_id = lb.condition_id
        ORDER BY lb.snapshot_ts DESC
        LIMIT {limit}
    """


def _runtime_console_query(*, limit: int) -> str:
    return f"""
        SELECT *
        FROM (
            SELECT
                started_at AS event_ts,
                '[INGEST] ' || COALESCE(source, 'unknown') || '/' || COALESCE(job_type, 'job')
                    || ' ' || COALESCE(status, 'unknown')
                    || ' seen=' || COALESCE(rows_seen, 0)::text
                    || ' written=' || COALESCE(rows_written, 0)::text AS line,
                CASE WHEN status = 'success' THEN 'info' ELSE 'warn' END AS severity
            FROM app.ingestion_logs
            UNION ALL
            SELECT
                started_at AS event_ts,
                '[PAPER] ' || strategy_name
                    || ' orders=' || attempted_orders::text
                    || ' fills=' || filled_orders::text
                    || ' pnl=' || net_pnl::text AS line,
                'info' AS severity
            FROM app.paper_trading_runs
            UNION ALL
            SELECT
                started_at AS event_ts,
                '[SHADOW] ' || strategy_name
                    || ' decisions=' || decision_count::text
                    || ' fills=' || theoretical_fill_count::text
                    || ' missed=' || missed_fill_count::text AS line,
                CASE WHEN missed_fill_count > 0 THEN 'warn' ELSE 'info' END AS severity
            FROM app.shadow_trading_runs
            UNION ALL
            SELECT
                generated_at AS event_ts,
                '[READINESS] ' || status
                    || ' score=' || live_readiness_score::text
                    || ' kill=' || kill_switch_state AS line,
                CASE WHEN status = 'ready' THEN 'info' ELSE 'warn' END AS severity
            FROM app.live_readiness_reports
        ) events
        ORDER BY event_ts DESC
        LIMIT {limit}
    """


def _recent_shadow_decisions_query(*, limit: int) -> str:
    return f"""
        SELECT decision_ts, market_id, asset_id, signal_type, action, status,
               fill_json->>'fill_possible' AS fill_possible,
               fill_json->>'filled_size' AS filled_size,
               fill_json->>'average_price' AS average_price,
               comparison_json->>'delay_ms' AS delay_ms,
               comparison_json->>'slippage_abs' AS slippage_abs
        FROM app.shadow_trading_decisions
        ORDER BY decision_ts DESC
        LIMIT {limit}
    """


def fetch_all(query: str, *args: Any) -> list[dict[str, Any]]:
    try:
        return asyncio.run(_fetch_all(query, *args))
    except Exception as exc:
        st.error(f"Database query failed: {exc}")
        return []


def fetch_one(query: str, *args: Any) -> dict[str, Any]:
    rows = fetch_all(query, *args)
    return rows[0] if rows else {}


async def _fetch_all(query: str, *args: Any) -> list[dict[str, Any]]:
    connection = await asyncpg.connect(_asyncpg_url(DATABASE_URL))
    try:
        rows = await connection.fetch(query, *args)
        return [dict(row) for row in rows]
    finally:
        await connection.close()


def api_health() -> str:
    try:
        with urlopen(API_HEALTH_URL, timeout=2) as response:
            return "ok" if response.status < 400 else "error"
    except Exception:
        return "error"


def to_frame(rows: list[dict[str, Any]]):
    if pd is None:
        return rows
    return pd.DataFrame(rows)


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return str(value)


def fmt_compact(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, datetime):
        return value.astimezone(UTC).strftime("%H:%M:%S")
    if isinstance(value, (Decimal, int, float)):
        number = float(value)
        if abs(number) >= 1000:
            return f"{number:,.0f}"
        if abs(number) >= 10:
            return f"{number:.2f}"
        return f"{number:.4f}".rstrip("0").rstrip(".")
    return str(value)


def fmt_money(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (Decimal, int, float)):
        return f"${float(value):,.2f}"
    return str(value)


def fmt_time(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).strftime("%H:%M:%S")
    return fmt_compact(value)


def age_label(value: Any) -> str:
    if not isinstance(value, datetime):
        return "n/a"
    timestamp = value if value.tzinfo else value.replace(tzinfo=UTC)
    age = datetime.now(UTC) - timestamp.astimezone(UTC)
    seconds = max(0, int(age.total_seconds()))
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    return f"{minutes // 60}h ago"


def fmt_len(value: Any) -> str:
    if isinstance(value, list):
        return str(len(value))
    return "0" if value is None else str(value)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug[:120] or "note"


def _asyncpg_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


if __name__ == "__main__":
    main()
