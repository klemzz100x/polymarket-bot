from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from html import escape
import json
import os
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

import asyncpg
import streamlit as st

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
            "Oracle Scan",
            "Daily Research",
            "Weather Markets",
            "End-of-Event",
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
            "Edge Research",
            "Twitter Research",
        ],
    )
    if page == "Terminal Cockpit":
        terminal_cockpit_page()
    elif page == "Oracle Scan":
        oracle_scan_page()
    elif page == "Daily Research":
        daily_research_page()
    elif page == "Weather Markets":
        weather_markets_page()
    elif page == "End-of-Event":
        end_of_event_page()
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
    elif page == "Edge Research":
        edge_research_page()
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

    render_cockpit_header(summary, readiness, equity, refresh_label)

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
        render_btc_5m_radar()
        render_weather_radar()
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
        data_table(result["notes"])

    st.subheader("Recent Twitter Source Notes")
    source_dir = OBSIDIAN_VAULT_DIR / "Sources" / "Twitter-Threads"
    notes = list_recent_markdown_notes(source_dir, limit=25)
    data_table(notes)


def oracle_scan_page() -> None:
    inject_terminal_css()
    st.subheader("Oracle Scan — Becker + Claude")
    st.caption("Signals from the Becker calibration + Claude oracle. Run `scan_becker_oracle.py --live --claude --obsidian` to refresh.")

    ORACLE_JSON = Path(os.getenv("ORACLE_SCAN_JSON", "tmp/becker_oracle_scan.json"))
    if not ORACLE_JSON.exists():
        st.warning(f"No scan file found at `{ORACLE_JSON}`. Run the scanner first.")
        st.code("PYTHONPATH=src python scripts/scan_becker_oracle.py --live --claude --min-volume 20000 --obsidian")
        return

    try:
        signals = json.loads(ORACLE_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        st.error(f"Failed to load scan: {exc}")
        return

    if not signals:
        st.info("No signals in last scan.")
        return

    scan_date = ORACLE_JSON.stat().st_mtime
    from datetime import datetime as _dt
    last_run = _dt.fromtimestamp(scan_date).strftime("%Y-%m-%d %H:%M")
    st.caption(f"Last scan: {last_run} | {len(signals)} signals")

    actionable = [s for s in signals if s.get("claude_edge") is not None and s["claude_edge"] > 0.03 and s.get("claude_confidence") in ("medium", "high") and s.get("recommended_side") in ("YES", "NO")]
    near_miss = [s for s in signals if s.get("claude_edge") is not None and 0 < s["claude_edge"] <= 0.03 and s.get("recommended_side") in ("YES", "NO")]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Signaux Becker", len(signals))
    col2.metric("Actionnables (>3%)", len(actionable))
    col3.metric("Near-miss", len(near_miss))
    best_edge = max((s["claude_edge"] for s in signals if s.get("claude_edge") is not None), default=0)
    col4.metric("Best ClEdge", f"{best_edge:+.2%}")

    if actionable:
        st.markdown("### Signaux actionnables (ClEdge >3%, confiance medium+)")
        rows = []
        for s in actionable:
            rows.append({
                "Question": s["question"][:60],
                "Prix": f"{s['market_price']:.1%}",
                "Side": s["recommended_side"],
                "BkrEdge": f"{s['becker_edge']:+.2%}",
                "ClEdge": f"{s['claude_edge']:+.2%}",
                "Kelly¼": f"{s['kelly_quarter']:.2%}",
                "Conf": s.get("claude_confidence", ""),
                "Vol$M": f"{s['volume_usd']/1e6:.1f}M",
            })
        data_table(rows, height=200)
        for s in actionable:
            with st.expander(f"[{s['recommended_side']}] {s['question'][:70]}"):
                st.write(f"**Prix** : {s['market_price']:.2%} | **ClEdge** : {s['claude_edge']:+.2%} | **Kelly¼** : {s['kelly_quarter']:.2%}")
                st.write(f"**Confiance** : {s.get('claude_confidence')} | **Volume** : ${s['volume_usd']:,.0f}")
                st.write("**Facteurs clés :**")
                for factor in (s.get("claude_key_factors") or []):
                    st.write(f"- {factor}")
                st.code(s["condition_id"])
    else:
        st.info("Aucun signal actionnable dans le dernier scan.")

    st.markdown("### Tous les signaux")
    all_rows = []
    for s in signals:
        cl = f"{s['claude_edge']:+.2%}" if s.get("claude_edge") is not None else "n/a"
        all_rows.append({
            "Question": s["question"][:55],
            "Prix": f"{s['market_price']:.1%}",
            "Side": s.get("recommended_side", ""),
            "BkrEdge": f"{s['becker_edge']:+.2%}",
            "ClEdge": cl,
            "Kelly¼": f"{s['kelly_quarter']:.2%}",
            "Conf": s.get("claude_confidence", ""),
            "Vol$M": f"{s['volume_usd']/1e6:.1f}M",
        })
    data_table(all_rows, height=360)


def daily_research_page() -> None:
    inject_terminal_css()
    st.subheader("Daily Research — Oracle + Smart Money")
    st.caption("Cross-referenced signals with conviction score. Run `run_daily_research.py --obsidian` to refresh.")

    DAILY_JSON = Path(os.getenv("DAILY_RESEARCH_JSON", "tmp/daily_research.json"))
    SIGNAL_LOG = Path("tmp/signal_log.json")

    if not DAILY_JSON.exists():
        st.warning(f"No daily research file at `{DAILY_JSON}`.")
        st.code("PYTHONPATH=src python scripts/run_daily_research.py --obsidian")
        return

    try:
        data = json.loads(DAILY_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        st.error(f"Failed to load: {exc}")
        return

    from datetime import datetime as _dt
    last_run = _dt.fromtimestamp(DAILY_JSON.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    actionable = data.get("actionable", [])
    all_signals = data.get("oracle_signals", [])
    sm_markets = data.get("smart_money_markets", 0)

    # Signal log stats
    log_total, log_resolved, log_accuracy = 0, 0, None
    if SIGNAL_LOG.exists():
        try:
            log = json.loads(SIGNAL_LOG.read_text(encoding="utf-8"))
            log_total = len(log)
            log_resolved = sum(1 for e in log if e.get("resolved"))
            correct = sum(1 for e in log if e.get("correct") is True)
            log_accuracy = correct / log_resolved if log_resolved else None
        except Exception:
            pass

    st.caption(f"Last run: {last_run} | Date: {data.get('date', '?')}")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Oracle signals", len(all_signals))
    col2.metric("Actionnables", len(actionable))
    col3.metric("SM markets", sm_markets)
    col4.metric("Signal log", log_total)
    col5.metric("Accuracy", f"{log_accuracy:.0%}" if log_accuracy else "—")

    if actionable:
        st.markdown("### Signaux cross-référencés (Oracle + Smart Money)")
        rows = []
        for s in actionable:
            sm = "✓" if s.get("sm_aligned") else ("✗" if s.get("sm_opposed") else "–")
            rows.append({
                "Question": s.get("question", "")[:55],
                "Side": s.get("recommended_side", ""),
                "ClEdge": f"{s['claude_edge']:+.2%}" if s.get("claude_edge") is not None else "n/a",
                "Conf": s.get("claude_confidence", ""),
                "SM": sm,
                "Score": f"{s.get('conviction_score', 0):.0f}",
                "Vol$M": f"{s.get('volume_usd', 0)/1e6:.1f}M",
            })
        data_table(rows, height=300)

        for s in actionable[:5]:
            sm_label = "ALIGNÉ ✓" if s.get("sm_aligned") else ("OPPOSÉ ✗" if s.get("sm_opposed") else "non suivi")
            with st.expander(f"[{s.get('recommended_side')}] Score {s.get('conviction_score', 0):.0f} — {s.get('question', '')[:65]}"):
                st.write(f"**ClEdge** : {s.get('claude_edge', 0):+.2%} | **Conf** : {s.get('claude_confidence')} | **Kelly¼** : {s.get('kelly_quarter', 0):.2%}")
                st.write(f"**Smart money** : {sm_label}")
                if s.get("sm_wallets"):
                    st.write(f"**Wallets** : {', '.join(s['sm_wallets'])}")
                for factor in (s.get("claude_key_factors") or []):
                    st.write(f"- {factor}")
                st.code(s.get("condition_id", ""))
    else:
        st.info("Aucun signal cross-référencé. Relancer le scanner.")

    if log_total:
        st.markdown("### Signal log")
        try:
            log_data = json.loads(SIGNAL_LOG.read_text(encoding="utf-8"))
            log_rows = []
            for e in sorted(log_data, key=lambda x: x.get("logged_at", ""), reverse=True)[:20]:
                log_rows.append({
                    "Date": e.get("scan_date", ""),
                    "Question": e.get("question", "")[:50],
                    "Side": e.get("side", ""),
                    "ClEdge": f"{e['claude_edge']:+.2%}" if e.get("claude_edge") is not None else "n/a",
                    "Score": f"{e.get('kelly_quarter', 0):.2%}" if e.get("kelly_quarter") else "—",
                    "Resolved": "✓" if e.get("resolved") else "○",
                    "Correct": "✓" if e.get("correct") is True else ("✗" if e.get("correct") is False else "—"),
                })
            data_table(log_rows, height=300)
        except Exception:
            pass


def weather_markets_page() -> None:
    inject_terminal_css()
    st.subheader("Weather Markets — SC-010")
    st.caption("Temperature bucket markets via Gamma slug API + Open-Meteo forecast. Run `scan_weather_markets.py --days 3 --obsidian` to refresh.")

    WEATHER_JSON = Path(os.getenv("WEATHER_SCAN_JSON", "tmp/weather_market_scan.json"))
    if not WEATHER_JSON.exists():
        st.warning(f"No weather scan at `{WEATHER_JSON}`.")
        st.code("PYTHONPATH=src python scripts/scan_weather_markets.py --days 3 --obsidian")
        return

    try:
        signals = json.loads(WEATHER_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        st.error(f"Failed to load: {exc}")
        return

    from datetime import datetime as _dt
    last_run = _dt.fromtimestamp(WEATHER_JSON.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    st.caption(f"Last scan: {last_run} | {len(signals)} opportunities found")

    if not signals:
        st.info("Aucune opportunité météo. Les marchés ont peut-être expiré ou les forecasts sont alignés.")
        return

    buy_yes = [s for s in signals if s.get("signal") == "BUY_YES"]
    buy_no = [s for s in signals if s.get("signal") == "BUY_NO"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Opportunités totales", len(signals))
    col2.metric("BUY YES", len(buy_yes))
    col3.metric("BUY NO", len(buy_no))

    st.markdown("### Signaux par edge décroissant")
    rows = []
    for s in signals:
        bucket_lo = s.get("bucket_low", -999)
        bucket_hi = s.get("bucket_high", 999)
        bucket_str = f"[{bucket_lo:.0f}–{bucket_hi:.0f}]" if bucket_hi < 900 else f"[{bucket_lo:.0f}+]"
        rows.append({
            "Ville": s.get("city", ""),
            "Date": s.get("target_date", ""),
            "Signal": s.get("signal", ""),
            "Prix YES": f"{s.get('yes_price', 0):.3f}",
            "Edge%": f"{s.get('edge_pct', 0):+.1f}%",
            "Forecast": f"{s.get('forecast_temp', 0):.1f}°C",
            "Bucket": bucket_str,
        })
    data_table(rows, height=300)

    st.markdown("### Détails")
    for s in signals[:5]:
        bucket_lo = s.get("bucket_low", -999)
        bucket_hi = s.get("bucket_high", 999)
        bucket_str = f"[{bucket_lo:.0f}–{bucket_hi:.0f}°C]" if bucket_hi < 900 else f"[{bucket_lo:.0f}°C+]"
        with st.expander(f"[{s.get('signal')}] {s.get('city')} {s.get('target_date')} {bucket_str} → edge {s.get('edge_pct', 0):+.1f}%"):
            st.write(f"**Forecast** : {s.get('forecast_temp')}°C | **Prix YES** : {s.get('yes_price', 0):.3f} | **Edge** : {s.get('edge_pct', 0):+.1f}%")
            st.write(f"**Rationale** : {s.get('rationale', '')}")
            st.write(f"⚠️ Edge théorique (forecast supposé exact). Incertitude forecast ~±1.5°C à prendre en compte.")
            st.code(s.get("condition_id", ""))

    st.markdown("---")
    st.caption("Slug pattern : `highest-temperature-in-{city}-on-{month}-{day}-{year}` | Source : @AlterEgo_eth")


def end_of_event_page() -> None:
    inject_terminal_css()
    st.subheader("End-of-Event Bias — SC-009")
    st.caption("Structural mispricing near resolution: LP withdrawal → favourite discounts + longshot premiums. Run `scan_end_of_event.py --obsidian` to refresh.")

    EOE_JSON = Path(os.getenv("EOE_SCAN_JSON", "tmp/end_of_event_signals.json"))
    if not EOE_JSON.exists():
        st.warning(f"No end-of-event scan at `{EOE_JSON}`.")
        st.code("PYTHONPATH=src python scripts/scan_end_of_event.py --max-hours 168 --obsidian")
        return

    try:
        signals = json.loads(EOE_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        st.error(f"Failed to load: {exc}")
        return

    from datetime import datetime as _dt
    last_run = _dt.fromtimestamp(EOE_JSON.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    st.caption(f"Last scan: {last_run} | {len(signals)} signals")

    if not signals:
        st.info("Aucun signal end-of-event. Marchés près de l'expiry manquants ou prix déjà extrêmes.")
        st.write("**Quand ce scanner est actif :** marchés esports/sports/weather expirables dans 24-72h avec prix 0.30–0.90.")
        return

    fav = [s for s in signals if s.get("edge_type") == "favourite_discount"]
    long = [s for s in signals if s.get("edge_type") == "longshot_premium"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total signaux", len(signals))
    col2.metric("Favourite discounts", len(fav), help="BUY YES — favoris bradés par panique")
    col3.metric("Longshot premiums", len(long), help="BUY NO — longshots surévalués par espoir")

    st.markdown("### Signaux (triés par edge)")
    rows = []
    for s in signals:
        type_label = "FAV-DISC" if s.get("edge_type") == "favourite_discount" else "LONG-PREM"
        rows.append({
            "Question": s.get("question", "")[:52],
            "Side": s.get("signal_side", ""),
            "Prix": f"{s.get('signal_price', 0):.3f}",
            "Edge%": f"{s.get('est_edge', 0):+.2%}",
            "Heures": f"{s.get('hours_left', 0):.1f}h",
            "Vol$K": f"{s.get('volume_usd', 0)/1000:.0f}K",
            "Type": type_label,
            "Cat": s.get("category", ""),
        })
    data_table(rows, height=300)

    st.markdown("### Référence théorique")
    st.write("**M(t) = α × σ × √(T-t) × (1/L(t))** — Mispricing augmente quand liquidité s'effondre près de la résolution.")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Wallets spécialistes end-of-event :**")
        st.write("- `0xec981ed...` — 0xheavy888 ($772K, 4579 trades)")
        st.write("- `0xb40e896...` — Poligarch ($132K, 20K trades)")
    with col2:
        st.write("**Setup optimal :**")
        st.write("- Marchés esports/sports < 72h expiry")
        st.write("- Volume < $50K (thin liquidity)")
        st.write("- Prix favori 0.65–0.92 (pas encore extrême)")


def edge_research_page() -> None:
    inject_terminal_css()
    st.subheader("Edge Research")
    st.caption("Thread-to-edge synthesis. Read-only view: candidates, evidence quality, and missing extraction work.")

    source_dir = OBSIDIAN_VAULT_DIR / "Sources" / "Twitter-Threads"
    registry_path = OBSIDIAN_VAULT_DIR / "Research" / "Strategy-Candidates" / "strategy-candidate-registry.json"
    synthesis_path = OBSIDIAN_VAULT_DIR / "Research" / "Edge-Research" / "twitter-edge-synthesis.md"
    full_matrix_path = RESOURCES_DIR / "twitter-threads" / "full-content" / "thread_value_matrix.json"

    source_notes = list_recent_markdown_notes(source_dir, limit=500)
    candidates = load_strategy_candidate_records(registry_path)
    families = aggregate_candidates_by_family(candidates)
    thread_statuses = aggregate_thread_status(source_dir)
    full_threads = load_full_thread_matrix(full_matrix_path)
    full_thread_families = aggregate_full_thread_families(full_threads)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Twitter notes", fmt_compact(len(source_notes)))
    col2.metric("Candidates", fmt_compact(len(candidates)))
    col3.metric("Full threads", fmt_compact(len(full_threads)))
    col4.metric("Edge families", fmt_compact(len(full_thread_families) or len(families)))

    st.markdown("**Full-thread edge map**")
    if full_threads:
        direct_edges = sum(1 for row in full_threads if row.get("relevance") == "direct_edge")
        high_priority = sum(1 for row in full_threads if row.get("priority") == "high")
        metric_cols = st.columns(4)
        metric_cols[0].metric("Direct edge threads", fmt_compact(direct_edges))
        metric_cols[1].metric("High priority", fmt_compact(high_priority))
        metric_cols[2].metric("Source JSON", "present")
        metric_cols[3].metric("Synthesis", "present" if synthesis_path.exists() else "missing")
        data_table(full_thread_families, height=260)
    else:
        st.info(f"No full-thread matrix found yet: `{full_matrix_path}`")

    left, right = st.columns([1.35, 1.0])
    with left:
        st.markdown("**Candidate registry family map**")
        data_table(families, height=300)
    with right:
        st.markdown("**Thread extraction status**")
        if not thread_statuses:
            st.caption("No Twitter notes found.")
        for row in thread_statuses:
            render_status_badge(str(row["status"]), row["count"])
        st.caption(f"Synthesis note: `{synthesis_path}`")
        st.caption(f"Full thread matrix: `{full_matrix_path}`")

    st.markdown("**Full-thread research backlog**")
    data_table(
        [
            {
                "priority": row.get("priority"),
                "relevance": row.get("relevance"),
                "primary_family": row.get("primary_family"),
                "author": row.get("author"),
                "title": row.get("title"),
                "first_action": first_item(row.get("actionable_takeaways")),
                "source": row.get("source"),
            }
            for row in full_threads
        ],
        height=360,
    )

    st.markdown("**Top strategy candidates**")
    data_table(candidates[:50], height=360)

    st.markdown("**Recent source notes**")
    data_table(source_notes[:50], height=300)


def inject_terminal_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ops-bg: #040301;
            --ops-panel: rgba(12, 9, 4, 0.92);
            --ops-line: rgba(247, 174, 57, 0.23);
            --ops-amber: #f5a623;
            --ops-green: #20ff68;
            --ops-red: #ff3b3b;
            --ops-blue: #5aa7ff;
            --ops-muted: rgba(247, 213, 150, 0.62);
        }
        .stApp {
            background:
                linear-gradient(rgba(255,176,45,0.025) 1px, transparent 1px),
                radial-gradient(circle at 50% 0%, rgba(245,166,35,0.08), transparent 34%),
                var(--ops-bg);
            background-size: 100% 18px, auto, auto;
            color: #f8dca3;
        }
        .block-container {
            padding-top: 0.7rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }
        h1, h2, h3, .stMarkdown, .stCaption, label, p, div {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            letter-spacing: 0;
        }
        header[data-testid="stHeader"] { background: transparent; }
        section[data-testid="stSidebar"] {
            background: #070501;
            border-right: 1px solid var(--ops-line);
        }
        section[data-testid="stSidebar"] * {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }
        div[data-testid="stMetric"] {
            border: 1px solid var(--ops-line);
            border-radius: 2px;
            padding: 0.52rem 0.6rem;
            background: linear-gradient(180deg, rgba(31,20,5,0.92), rgba(8,6,2,0.96));
            box-shadow: inset 0 0 18px rgba(245,166,35,0.05);
            min-height: 78px;
        }
        div[data-testid="stMetricLabel"] p {
            color: var(--ops-muted);
            font-size: 0.68rem;
            text-transform: uppercase;
        }
        div[data-testid="stMetricValue"] {
            color: var(--ops-amber);
            font-size: 1.28rem;
            text-shadow: 0 0 12px rgba(245,166,35,0.26);
        }
        div[data-testid="stMetricDelta"] {
            color: var(--ops-green);
            font-size: 0.72rem;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--ops-line);
            border-radius: 2px;
            background: rgba(9,7,3,0.78);
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(245,166,35,0.16);
            box-shadow: inset 0 0 24px rgba(0,0,0,0.34);
        }
        .stProgress > div > div > div {
            background-color: var(--ops-green);
        }
        .ops-header {
            border: 1px solid var(--ops-line);
            border-radius: 2px;
            background: linear-gradient(180deg, rgba(18,12,3,0.96), rgba(5,4,1,0.98));
            padding: 0.55rem 0.75rem;
            margin-bottom: 0.65rem;
            box-shadow: 0 0 28px rgba(245,166,35,0.08);
        }
        .ops-topline {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 1rem;
            align-items: center;
            border-bottom: 1px solid rgba(245,166,35,0.18);
            padding-bottom: 0.35rem;
        }
        .ops-brand {
            color: var(--ops-amber);
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .ops-live {
            color: var(--ops-green);
            font-size: 0.72rem;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .ops-grid {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 0.6rem;
            padding-top: 0.5rem;
        }
        .ops-cell {
            border-left: 1px solid rgba(245,166,35,0.18);
            padding-left: 0.55rem;
            min-width: 0;
        }
        .ops-label {
            color: var(--ops-muted);
            font-size: 0.64rem;
            text-transform: uppercase;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .ops-value {
            color: var(--ops-amber);
            font-size: 1.08rem;
            font-weight: 700;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .ops-value.green { color: var(--ops-green); }
        .ops-value.red { color: var(--ops-red); }
        .ops-value.blue { color: var(--ops-blue); }
        .terminal-line {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.74rem;
            border-bottom: 1px solid rgba(245,166,35,0.09);
            padding: 0.22rem 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .terminal-good { color: var(--ops-green); }
        .terminal-warn { color: var(--ops-amber); }
        .terminal-bad { color: var(--ops-red); }
        .terminal-muted { color: var(--ops-muted); }
        @media (max-width: 900px) {
            .ops-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .ops-topline { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_cockpit_header(
    summary: dict[str, Any], readiness: dict[str, Any], equity: dict[str, Any], refresh_label: str
) -> None:
    now = datetime.now(UTC).strftime("%H:%M:%S UTC")
    api = api_health()
    live_mode = os.getenv("LIVE_EXECUTION_MODE", "DISABLED")
    live_class = "green" if live_mode == "DISABLED" else "red"
    cells = [
        ("API", api, "green" if api == "ok" else "red"),
        ("EQUITY", fmt_money(equity.get("equity")), ""),
        ("NET PNL", fmt_money(summary.get("net_pnl")), "green"),
        ("SNAPSHOTS", fmt_compact(summary.get("snapshots")), "blue"),
        ("READINESS", fmt_compact(readiness.get("status")), "green"),
        ("LIVE MODE", live_mode, live_class),
    ]
    cell_html = "".join(
        f"<div class='ops-cell'><div class='ops-label'>{escape(label)}</div>"
        f"<div class='ops-value {css}'>{escape(str(value))}</div></div>"
        for label, value, css in cells
    )
    st.markdown(
        f"""
        <div class="ops-header">
            <div class="ops-topline">
                <div class="ops-brand">POLYBOT COCKPIT // PAPER + SHADOW OPS</div>
                <div class="ops-live">READ ONLY // AUTO {escape(refresh_label)} // {escape(now)}</div>
            </div>
            <div class="ops-grid">{cell_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(label: str, value: Any) -> None:
    normalized = label.lower()
    css_class = "terminal-muted"
    if normalized in {"candidate_ready", "content_rich"}:
        css_class = "terminal-good"
    elif normalized in {"needs_extraction", "placeholder", "raw_url_only", "missing"}:
        css_class = "terminal-warn"
    st.markdown(
        f"<div class='terminal-line {css_class}'><strong>{escape(label)}</strong>: {escape(str(value))}</div>",
        unsafe_allow_html=True,
    )


def maybe_auto_refresh(seconds: int) -> None:
    if seconds <= 0:
        return
    st.html(
        f"""
        <script>
        setTimeout(function() {{
            window.parent.location.reload();
        }}, {seconds * 1000});
        </script>
        """
    )


def render_compact_table(title: str, rows: list[dict[str, Any]], *, height: int) -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        frame = to_frame(rows)
        if pd is not None and frame.empty:
            st.caption("empty")
        else:
            data_table(frame, height=height)


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


def render_btc_5m_radar() -> None:
    latest = fetch_one(
        """
        SELECT observed_at, condition_id, market_slug, market_title, binance_price,
               binance_change_30s_pct, up_ask, down_ask, pair_cost, spread,
               market_state, rejected_reason, has_latency_signal, has_pair_arb_signal
        FROM app.btc_5m_monitor_ticks
        ORDER BY observed_at DESC
        LIMIT 1
        """
    )
    summary = fetch_one(
        """
        SELECT
            COUNT(*) AS ticks,
            COUNT(DISTINCT condition_id) AS markets,
            COUNT(*) FILTER (WHERE market_state = 'SIGNAL') AS signals,
            COUNT(*) FILTER (WHERE market_state = 'TRADEABLE') AS tradeable,
            COUNT(*) FILTER (WHERE market_state = 'ILLIQUID') AS illiquid,
            MIN(spread) AS best_spread,
            MAX(abs(binance_change_30s_pct)) AS max_abs_btc_move_30s
        FROM app.btc_5m_monitor_ticks
        WHERE observed_at > now() - interval '24 hours'
        """
    )
    recent = fetch_all(
        """
        SELECT observed_at, market_state, binance_change_30s_pct, spread, pair_cost,
               up_ask, down_ask, rejected_reason
        FROM app.btc_5m_monitor_ticks
        ORDER BY observed_at DESC
        LIMIT 12
        """
    )

    with st.container(border=True):
        st.markdown("**BTC 5M Radar**")
        if not latest:
            st.caption("No BTC 5-min monitor ticks yet. Run `scripts/monitor_btc_5min.py` to feed this panel.")
            return

        cols = st.columns(6)
        cols[0].metric("State", fmt_compact(latest.get("market_state")))
        cols[1].metric("BTC", fmt_money(latest.get("binance_price")))
        cols[2].metric("BTC 30s", f"{fmt_compact(latest.get('binance_change_30s_pct'))}%")
        cols[3].metric("Spread", fmt_pct(latest.get("spread")))
        cols[4].metric("YES+NO", fmt_compact(latest.get("pair_cost")))
        cols[5].metric("Signals 24h", fmt_compact(summary.get("signals")))

        state = str(latest.get("market_state") or "")
        css_class = {
            "SIGNAL": "terminal-good",
            "TRADEABLE": "terminal-good",
            "WATCH": "terminal-warn",
            "ILLIQUID": "terminal-bad",
            "NO_BOOK": "terminal-muted",
        }.get(state, "terminal-muted")
        status_text = (
            f"{fmt_time(latest.get('observed_at'))} {latest.get('market_slug')} "
            f"{state} | {latest.get('rejected_reason') or 'no rejection'}"
        )
        st.markdown(
            f"<div class='terminal-line {css_class}'>{escape(status_text)}</div>",
            unsafe_allow_html=True,
        )

        stat_cols = st.columns(5)
        stat_cols[0].metric("Ticks 24h", fmt_compact(summary.get("ticks")))
        stat_cols[1].metric("Markets 24h", fmt_compact(summary.get("markets")))
        stat_cols[2].metric("Tradeable", fmt_compact(summary.get("tradeable")))
        stat_cols[3].metric("Illiquid", fmt_compact(summary.get("illiquid")))
        stat_cols[4].metric("Max BTC move", f"{fmt_compact(summary.get('max_abs_btc_move_30s'))}%")

        data_table(recent, height=210)


def render_weather_radar() -> None:
    latest = fetch_one(
        """
        SELECT observed_at, scan_id, market_state, weather_family, question,
               location_hint, threshold_hint, best_yes_ask, best_no_ask,
               pair_cost, spread, rejected_reason, edge_hypothesis
        FROM app.weather_market_radar_ticks
        ORDER BY observed_at DESC, spread ASC NULLS LAST
        LIMIT 1
        """
    )
    summary = fetch_one(
        """
        WITH latest_scan AS (
            SELECT scan_id
            FROM app.weather_market_radar_ticks
            ORDER BY observed_at DESC
            LIMIT 1
        )
        SELECT
            COUNT(*) AS markets,
            COUNT(*) FILTER (WHERE market_state = 'FORECAST_WATCH') AS forecast_watch,
            COUNT(*) FILTER (WHERE market_state = 'PAIR_ARB_WATCH') AS pair_arb_watch,
            COUNT(*) FILTER (WHERE market_state = 'WATCH') AS watch,
            COUNT(*) FILTER (WHERE market_state = 'NO_BOOK') AS no_book,
            MIN(spread) AS best_spread,
            MAX(observed_at) AS latest_scan_at
        FROM app.weather_market_radar_ticks
        WHERE scan_id = (SELECT scan_id FROM latest_scan)
        """
    )
    rows = fetch_all(
        """
        WITH latest_scan AS (
            SELECT scan_id
            FROM app.weather_market_radar_ticks
            ORDER BY observed_at DESC
            LIMIT 1
        )
        SELECT market_state, spread, weather_family, location_hint, threshold_hint,
               LEFT(question, 86) AS question, rejected_reason
        FROM app.weather_market_radar_ticks
        WHERE scan_id = (SELECT scan_id FROM latest_scan)
        ORDER BY
            CASE market_state
                WHEN 'PAIR_ARB_WATCH' THEN 0
                WHEN 'FORECAST_WATCH' THEN 1
                WHEN 'WATCH' THEN 2
                WHEN 'ILLIQUID' THEN 3
                ELSE 9
            END,
            spread ASC NULLS LAST
        LIMIT 14
        """
    )
    forecast_summary = fetch_one(
        """
        SELECT
            COUNT(*) AS scored,
            COUNT(*) FILTER (WHERE model_state = 'EDGE_CANDIDATE') AS edge_candidates,
            MAX(GREATEST(COALESCE(edge_yes, -99), COALESCE(edge_no, -99))) AS best_proxy_edge,
            MAX(observed_at) AS latest_score_at
        FROM app.weather_forecast_edges
        WHERE observed_at > now() - interval '24 hours'
        """
    )
    forecast_edges = fetch_all(
        """
        SELECT model_state, action_bias, fair_yes, market_mid, edge_yes, edge_no,
               forecast_max_c, location_hint, LEFT(question, 78) AS question, reason,
               raw->>'source_adapter' AS source_adapter
        FROM app.weather_forecast_edges
        WHERE observed_at = (
            SELECT MAX(observed_at)
            FROM app.weather_forecast_edges
        )
        ORDER BY
            CASE model_state
                WHEN 'EDGE_CANDIDATE' THEN 0
                WHEN 'MODEL_WATCH' THEN 1
                WHEN 'FAIR_ALIGNED' THEN 2
                ELSE 9
            END,
            GREATEST(COALESCE(edge_yes, -99), COALESCE(edge_no, -99)) DESC
        LIMIT 8
        """
    )
    live_gate = fetch_one(
        """
        SELECT status, score, generated_at, blockers
        FROM app.weather_live_gate_reports
        ORDER BY generated_at DESC
        LIMIT 1
        """
    )
    station_observations = fetch_all(
        """
        SELECT station_id, temp_c, report_time, collected_at, LEFT(raw_metar, 96) AS raw_metar
        FROM app.weather_station_observations
        ORDER BY collected_at DESC, station_id
        LIMIT 6
        """
    )

    with st.container(border=True):
        st.markdown("**Weather Edge Radar**")
        if not latest:
            st.caption("No weather scan yet. Run `scripts/discover_weather_markets.py --obsidian`.")
            return

        cols = st.columns(6)
        cols[0].metric("State", fmt_compact(latest.get("market_state")))
        cols[1].metric("Markets", fmt_compact(summary.get("markets")))
        cols[2].metric("Forecast watch", fmt_compact(summary.get("forecast_watch")))
        cols[3].metric("Pair arb watch", fmt_compact(summary.get("pair_arb_watch")))
        cols[4].metric("Best spread", fmt_pct(summary.get("best_spread")))
        cols[5].metric("Proxy edges", fmt_compact(forecast_summary.get("edge_candidates")))

        state = str(latest.get("market_state") or "")
        css_class = {
            "PAIR_ARB_WATCH": "terminal-good",
            "FORECAST_WATCH": "terminal-good",
            "WATCH": "terminal-warn",
            "ILLIQUID": "terminal-bad",
            "NO_BOOK": "terminal-muted",
            "NO_TOKENS": "terminal-muted",
        }.get(state, "terminal-muted")
        text = (
            f"{fmt_time(latest.get('observed_at'))} {state} "
            f"{latest.get('weather_family') or ''} | "
            f"{latest.get('location_hint') or 'global'} | "
            f"{latest.get('question') or ''}"
        )
        st.markdown(
            f"<div class='terminal-line {css_class}'>{escape(text)}</div>",
            unsafe_allow_html=True,
        )
        st.caption(latest.get("edge_hypothesis") or latest.get("rejected_reason") or "")
        data_table(rows, height=230)
        if forecast_edges:
            st.markdown("**Forecast proxy scores**")
            score_cols = st.columns(3)
            score_cols[0].metric("Scored 24h", fmt_compact(forecast_summary.get("scored")))
            score_cols[1].metric("Edge candidates", fmt_compact(forecast_summary.get("edge_candidates")))
            score_cols[2].metric("Best proxy edge", fmt_pct(forecast_summary.get("best_proxy_edge")))
            data_table(forecast_edges, height=190)
        st.markdown("**Weather live gate**")
        gate_cols = st.columns(4)
        gate_cols[0].metric("Gate", fmt_compact(live_gate.get("status")))
        gate_cols[1].metric("Score", fmt_compact(live_gate.get("score")))
        gate_cols[2].metric("Generated", age_label(live_gate.get("generated_at")))
        gate_cols[3].metric("Station reads", fmt_compact(len(station_observations)))
        if live_gate.get("blockers"):
            st.caption(f"Blockers: {live_gate.get('blockers')}")
        if station_observations:
            data_table(station_observations, height=160)


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


def load_strategy_candidate_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    records: list[dict[str, Any]] = []
    for item in payload.get("records", []):
        candidate = item.get("candidate", {})
        records.append(
            {
                "rank_score": item.get("rank_score"),
                "status": item.get("status", "new"),
                "name": candidate.get("name"),
                "edge_family": candidate.get("edge_family"),
                "priority": candidate.get("priority"),
                "difficulty": candidate.get("implementation_difficulty"),
                "summary": candidate.get("summary"),
                "next_action": candidate.get("next_action"),
                "source": candidate.get("source_obsidian_path"),
            }
        )
    return records


def aggregate_candidates_by_family(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        family = str(candidate.get("edge_family") or "unknown")
        group = groups.setdefault(
            family,
            {
                "edge_family": family,
                "candidates": 0,
                "high_priority": 0,
                "best_rank": 0,
                "next_action": candidate.get("next_action"),
            },
        )
        group["candidates"] += 1
        group["high_priority"] += 1 if candidate.get("priority") == "high" else 0
        group["best_rank"] = max(int(group["best_rank"] or 0), int(candidate.get("rank_score") or 0))
        if not group.get("next_action") and candidate.get("next_action"):
            group["next_action"] = candidate.get("next_action")
    return sorted(groups.values(), key=lambda row: (-row["best_rank"], row["edge_family"]))


def load_full_thread_matrix(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def aggregate_full_thread_families(threads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for thread in threads:
        families = thread.get("families")
        if not isinstance(families, list) or not families:
            families = [thread.get("primary_family") or "unclassified"]
        for family_value in families:
            family = str(family_value or "unclassified")
            group = groups.setdefault(
                family,
                {
                    "edge_family": family,
                    "threads": 0,
                    "high_priority": 0,
                    "direct_edge": 0,
                    "research_edge": 0,
                    "infrastructure_edge": 0,
                    "first_action": first_item(thread.get("actionable_takeaways")),
                },
            )
            group["threads"] += 1
            group["high_priority"] += 1 if thread.get("priority") == "high" else 0
            group["direct_edge"] += 1 if thread.get("relevance") == "direct_edge" else 0
            group["research_edge"] += 1 if thread.get("relevance") == "research_edge" else 0
            group["infrastructure_edge"] += 1 if thread.get("relevance") == "infrastructure_edge" else 0
            if not group.get("first_action"):
                group["first_action"] = first_item(thread.get("actionable_takeaways"))
    return sorted(groups.values(), key=lambda row: (-row["high_priority"], -row["threads"], row["edge_family"]))


def first_item(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0])
    if value:
        return str(value)
    return ""


def aggregate_thread_status(directory: Path) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    if not directory.exists():
        return []
    for path in directory.glob("*.md"):
        status = classify_thread_note(path)
        counts[status] = counts.get(status, 0) + 1
    return [{"status": status, "count": count} for status, count in sorted(counts.items())]


def classify_thread_note(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8").lower()
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1").lower()
    if "a completer apres extraction" in text or "a extraire" in text:
        return "placeholder"
    if "research tasks" in text and "strategy candidate hooks" in text and "hypothesis:\n-" not in text:
        return "needs_extraction"
    if len(text.strip()) < 900:
        return "raw_url_only"
    if any(keyword in text for keyword in ("hypothesis", "testable signal", "backtest", "queue", "orderbook")):
        return "candidate_ready"
    return "content_rich"


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
    data_table(fetch_all(_latest_runs_query()))

    st.subheader("Freshest Market Data")
    data_table(fetch_all(_market_coverage_query(limit=20)))

    st.subheader("Recent Signals")
    data_table(fetch_all(_recent_signals_query(limit=50)))


def data_coverage_page() -> None:
    coverage = fetch_all(_market_coverage_query(limit=200))
    st.subheader("Market Data Coverage")
    data_table(coverage)

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
    data_table(logs)

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
    data_table(books)


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
        data_table(frame)

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
        data_table(drawdown)


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
    data_table(rows)


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
    data_table(rows)

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
    data_table(spreads)


def signals_page() -> None:
    rows = fetch_all(
        _recent_signals_query(limit=200)
    )
    st.subheader("Latest Signals")
    data_table(rows)

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
    data_table(signal_counts)

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
    data_table(hit_rows)


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
    data_table(exposure_rows)

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
    data_table(rejections)


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
    data_table(logs)

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
    data_table(stale)


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
    data_table(runs)

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
    data_table(decisions)


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
    data_table(reports)

    events = fetch_all(
        """
        SELECT event_ts, state, trigger, severity, reason, metadata
        FROM app.kill_switch_events
        ORDER BY event_ts DESC
        LIMIT 100
        """
    )
    st.subheader("Kill Switch Events")
    data_table(events)


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
    data_table(quality)

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
    data_table(spreads)

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
    data_table(stale)

    live_quality = fetch_all(
        """
        SELECT status, accepted, reason, created_at, client_order_id, exchange_order_id
        FROM app.live_execution_reports
        ORDER BY created_at DESC
        LIMIT 100
        """
    )
    st.subheader("Live Execution Reports")
    data_table(live_quality)


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
    data_table(latest.get("balances") or [])
    st.subheader("Positions")
    data_table(latest.get("positions") or [])
    st.subheader("Open Orders")
    data_table(latest.get("open_orders") or [])

    history = fetch_all(
        """
        SELECT wallet_address, captured_at, total_exposure_usd
        FROM app.wallet_snapshots
        ORDER BY captured_at DESC
        LIMIT 100
        """
    )
    st.subheader("Wallet Sync History")
    data_table(history)


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
    data_table(orders)

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
    data_table(fills)

    risk_events = fetch_all(
        """
        SELECT event_ts, client_order_id, market_id, strategy_name, allowed, reason, checks
        FROM app.live_risk_events
        ORDER BY event_ts DESC
        LIMIT 200
        """
    )
    st.subheader("Risk Gate Events")
    data_table(risk_events)

    reconciliation = fetch_all(
        """
        SELECT generated_at, status, checked_orders, exchange_open_orders, report
        FROM app.oms_reconciliation_reports
        ORDER BY generated_at DESC
        LIMIT 100
        """
    )
    st.subheader("Reconciliation")
    data_table(reconciliation)


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
    return pd.DataFrame(_normalize_for_table(rows))


def data_table(rows: Any, *, height: int | None = None) -> None:
    frame = rows if pd is not None and hasattr(rows, "empty") else to_frame(rows)
    kwargs: dict[str, Any] = {"width": "stretch"}
    if height is not None:
        kwargs["height"] = height
    st.dataframe(frame, **kwargs)


def _normalize_for_table(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value
    if isinstance(value, dict):
        return {key: _normalize_for_table(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_for_table(item) for item in value]
    return value


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


def fmt_pct(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (Decimal, int, float)):
        return f"{float(value) * 100:.2f}%"
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
