from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from html import escape
import json
import os
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import asyncpg
import streamlit as st

try:
    import pandas as pd
except ImportError:
    pd = None

st.set_page_config(page_title="Polybot // Copy Trading", layout="wide", initial_sidebar_state="collapsed")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://polymarket:change-me@postgres:5432/polymarket")
POLYMARKET_DATA_API = "https://data-api.polymarket.com"
POLYCOP_WALLET = os.getenv("POLYCOP_WALLET_ADDRESS", "")
WALLET_CONF_JSON = Path(os.getenv("WALLET_CONF_JSON", "tmp/wallet_confidence.json"))

WATCHLIST = [
    {"label": "aenews2",    "strategy": "Overreaction fader", "pnl": "$1.94M", "tier": "T1", "addr": "0x44c1dfe4"},
    {"label": "YatSen",     "strategy": "Anchoring bias",     "pnl": "$2.3M",  "tier": "T1", "addr": "0x5bffcf56"},
    {"label": "ImJustKen",  "strategy": "Reflexivity",        "pnl": "$3.03M", "tier": "T1", "addr": "0x9d84ce03"},
    {"label": "Poligarch",  "strategy": "Longshot fader",     "pnl": "$133k",  "tier": "T1", "addr": "0xb40e8967"},
    {"label": "0xheavy888", "strategy": "End-of-event",       "pnl": "$772k",  "tier": "T2", "addr": "0xec981ed7"},
]


# ── CSS ──────────────────────────────────────────────────────────────────────

def inject_css() -> None:
    st.markdown("""
    <style>
    :root {
        --bg:     #000000;
        --panel:  #0a0a0a;
        --border: rgba(0,255,100,0.12);
        --green:  #00ff68;
        --red:    #ff3b3b;
        --amber:  #f5a623;
        --muted:  rgba(200,255,220,0.4);
        --text:   #c8ffd8;
    }
    .stApp {
        background: var(--bg);
        color: var(--text);
    }
    .block-container { padding: 0.6rem 1.2rem 1rem; max-width: 100%; }
    * { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace !important; }
    header[data-testid="stHeader"],
    section[data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 2px;
        padding: 0.5rem 0.7rem;
        min-height: 72px;
    }
    div[data-testid="stMetricLabel"] p  { color: var(--muted);  font-size: 0.65rem; text-transform: uppercase; }
    div[data-testid="stMetricValue"]    { color: var(--green);  font-size: 1.2rem;  font-weight: 700; }
    div[data-testid="stMetricDelta"]    { color: var(--amber);  font-size: 0.7rem; }
    div[data-testid="stDataFrame"]      { border: 1px solid var(--border); background: var(--panel); }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--border); background: var(--panel); }
    /* chart background */
    div[data-testid="stArrowVegaLiteChart"] > div { background: var(--panel) !important; }
    .hdr {
        display: grid; grid-template-columns: 1fr auto;
        align-items: center;
        border: 1px solid var(--border);
        border-radius: 2px;
        background: var(--panel);
        padding: 0.5rem 0.8rem;
        margin-bottom: 0.6rem;
        box-shadow: 0 0 24px rgba(0,255,100,0.04);
    }
    .hdr-brand { color: var(--green); font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; }
    .hdr-time  { color: var(--muted); font-size: 0.68rem; }
    .big-pnl {
        font-size: 2.6rem; font-weight: 700; text-align: center;
        padding: 0.3rem 0; letter-spacing: -0.02em; line-height: 1;
    }
    .big-pnl.pos { color: var(--green); text-shadow: 0 0 18px rgba(0,255,104,0.4); }
    .big-pnl.neg { color: var(--red);   text-shadow: 0 0 18px rgba(255,59,59,0.35); }
    .section-label {
        color: var(--muted); font-size: 0.62rem; text-transform: uppercase;
        letter-spacing: 0.12em; margin-bottom: 0.3rem;
    }
    .wallet-row {
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid rgba(0,255,100,0.07);
        padding: 0.28rem 0; font-size: 0.74rem;
    }
    .w-label  { color: var(--green); font-weight: 700; min-width: 90px; }
    .w-strat  { color: var(--muted); flex: 1; padding: 0 0.5rem; }
    .w-pnl    { color: var(--amber); min-width: 60px; text-align: right; }
    .w-tier   { color: var(--muted); font-size: 0.6rem; min-width: 24px; text-align: right; }
    .pos-row {
        display: grid; grid-template-columns: 1fr 50px 60px 70px 70px;
        gap: 0.3rem; align-items: center;
        border-bottom: 1px solid rgba(0,255,100,0.07);
        padding: 0.25rem 0; font-size: 0.72rem;
    }
    .pos-title { color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .pos-side  { font-weight: 700; }
    .pos-yes   { color: var(--green); }
    .pos-no    { color: var(--red); }
    .pos-size  { color: var(--muted); text-align: right; }
    .pos-entry { color: var(--muted); text-align: right; }
    .pos-pnl-pos { color: var(--green); text-align: right; font-weight: 700; }
    .pos-pnl-neg { color: var(--red);   text-align: right; font-weight: 700; }
    @media (max-width: 800px) { .pos-row { grid-template-columns: 1fr 50px 70px; } }
    </style>
    """, unsafe_allow_html=True)


# ── DATA ─────────────────────────────────────────────────────────────────────

def fetch_polycop_pnl(wallet: str) -> dict:
    if not wallet:
        return {}
    try:
        url = f"{POLYMARKET_DATA_API}/positions?user={wallet}&limit=500"
        with urlopen(url, timeout=8) as r:
            positions = json.loads(r.read().decode())
        if not isinstance(positions, list):
            return {"error": "bad response"}
        realized = sum(float(p.get("realizedPnl") or 0) for p in positions)
        cash     = sum(float(p.get("cashPnl") or 0) for p in positions)
        return {
            "total_pnl":    realized + cash,
            "realized_pnl": realized,
            "open_pnl":     cash,
            "n_positions":  len(positions),
            "n_open":       sum(1 for p in positions if float(p.get("size") or 0) > 0),
            "positions":    positions,
        }
    except Exception as exc:
        return {"error": str(exc)}


def load_wallet_conf() -> dict | None:
    if not WALLET_CONF_JSON.exists():
        return None
    try:
        return json.loads(WALLET_CONF_JSON.read_text(encoding="utf-8"))
    except Exception:
        return None


def fetch_equity_curve() -> list[dict]:
    try:
        return asyncio.run(_fetch_equity())
    except Exception:
        return []


async def _fetch_equity() -> list[dict]:
    conn = await asyncpg.connect(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    try:
        rows = await conn.fetch("""
            SELECT snapshot_ts, SUM(equity) AS equity, SUM(net_pnl) AS net_pnl
            FROM app.paper_equity_snapshots
            GROUP BY snapshot_ts
            ORDER BY snapshot_ts ASC
            LIMIT 1000
        """)
        return [dict(r) for r in rows]
    finally:
        await conn.close()


# ── AUTO-REFRESH ──────────────────────────────────────────────────────────────

def auto_refresh(seconds: int) -> None:
    if seconds > 0:
        st.html(f"<script>setTimeout(()=>window.parent.location.reload(),{seconds*1000});</script>")


# ── RENDER ────────────────────────────────────────────────────────────────────

def fmt_pnl(v: Any) -> str:
    if v is None:
        return "—"
    f = float(v)
    return f"+${f:,.2f}" if f >= 0 else f"-${abs(f):,.2f}"


def render_header(total_pnl: float | None, n_open: int, n_wallets: int) -> None:
    now  = datetime.now(UTC).strftime("%H:%M:%S UTC")
    pnl  = fmt_pnl(total_pnl)
    st.markdown(
        f"""<div class="hdr">
            <div class="hdr-brand">POLYBOT // COPY TRADING &nbsp;|&nbsp;
                PNL: {escape(pnl)} &nbsp;|&nbsp;
                POSITIONS: {n_open} &nbsp;|&nbsp;
                WALLETS: {n_wallets}
            </div>
            <div class="hdr-time">&#9679; LIVE &nbsp; {escape(now)}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_pnl_block(data: dict) -> None:
    total    = data.get("total_pnl", 0)
    pnl_cls  = "pos" if total >= 0 else "neg"
    st.markdown(
        f"<div class='big-pnl {pnl_cls}'>{escape(fmt_pnl(total))}</div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Realized",  fmt_pnl(data.get("realized_pnl")))
    c2.metric("Open MTM",  fmt_pnl(data.get("open_pnl")))
    c3.metric("Positions", str(data.get("n_open", "—")))


def render_equity_chart(data: dict) -> None:
    hist_key = "eq_hist"
    if hist_key not in st.session_state:
        st.session_state[hist_key] = []

    hist: list[dict] = st.session_state[hist_key]
    total = data.get("total_pnl")
    if total is not None:
        hist.append({"t": datetime.now(UTC).strftime("%H:%M:%S"), "PnL": round(float(total), 2)})
        if len(hist) > 200:
            hist.pop(0)

    db_rows = fetch_equity_curve()
    if db_rows and pd is not None:
        df = pd.DataFrame(db_rows)[["snapshot_ts", "net_pnl"]].rename(columns={"net_pnl": "PnL", "snapshot_ts": "t"})
        df["t"] = pd.to_datetime(df["t"]).dt.strftime("%H:%M:%S")
    elif len(hist) >= 2 and pd is not None:
        df = pd.DataFrame(hist)
    else:
        df = None

    if df is not None and pd is not None and not df.empty:
        st.line_chart(df.set_index("t")["PnL"], height=210, color="#00ff68")
    else:
        st.caption("Accumulation en cours…")


def render_wallets(wallet_conf: dict | None) -> None:
    st.markdown("<div class='section-label'>Wallets copiés</div>", unsafe_allow_html=True)

    if wallet_conf:
        scores = wallet_conf.get("scores", [])
        qualified = [s for s in scores if s.get("confidence", 0) >= 55 and "BLACK" not in s.get("risk_badge", "")]
        display = [
            {
                "label":    (s.get("label") or s.get("address", "")[:10])[:18],
                "strategy": s.get("edge_type", "—").replace("category_specialist:", "")[:24],
                "conf":     s.get("confidence", 0),
                "pnl":      f"${float(s.get('diagnostics', {}).get('total_pnl_usd') or 0):+,.0f}",
                "badge":    s.get("risk_badge", "").split()[0],
            }
            for s in qualified[:8]
        ]
    else:
        display = [
            {"label": w["label"], "strategy": w["strategy"], "conf": "—", "pnl": w["pnl"], "badge": w["tier"]}
            for w in WATCHLIST
        ]

    for w in display:
        st.markdown(
            f"""<div class="wallet-row">
                <span class="w-label">{escape(str(w['label']))}</span>
                <span class="w-strat">{escape(str(w['strategy']))}</span>
                <span class="w-pnl">{escape(str(w['pnl']))}</span>
                <span class="w-tier">{escape(str(w['badge']))}</span>
            </div>""",
            unsafe_allow_html=True,
        )


def render_positions(positions: list[dict]) -> None:
    st.markdown("<div class='section-label'>Positions ouvertes</div>", unsafe_allow_html=True)
    if not positions:
        st.caption("Aucune position — configure POLYCOP_WALLET_ADDRESS dans .env")
        return

    open_pos = sorted(
        [p for p in positions if float(p.get("size") or 0) > 0],
        key=lambda p: abs(float(p.get("realizedPnl") or 0) + float(p.get("cashPnl") or 0)),
        reverse=True,
    )[:25]

    st.markdown("""<div class="pos-row" style="color:var(--muted);font-size:0.6rem;text-transform:uppercase">
        <span>Marché</span><span>Side</span><span style="text-align:right">Size</span>
        <span style="text-align:right">Prix</span><span style="text-align:right">PnL</span>
    </div>""", unsafe_allow_html=True)

    for p in open_pos:
        title   = (p.get("title") or p.get("market") or "—")[:52]
        outcome = p.get("outcome", "—")
        size    = float(p.get("size") or 0)
        price   = float(p.get("curPrice") or p.get("avgPrice") or 0)
        pnl_val = float(p.get("realizedPnl") or 0) + float(p.get("cashPnl") or 0)
        side_cls = "pos-yes" if outcome == "Yes" else "pos-no"
        pnl_cls  = "pos-pnl-pos" if pnl_val >= 0 else "pos-pnl-neg"
        st.markdown(
            f"""<div class="pos-row">
                <span class="pos-title">{escape(title)}</span>
                <span class="pos-side {side_cls}">{escape(outcome)}</span>
                <span class="pos-size">{size:.1f}</span>
                <span class="pos-entry">{price:.3f}</span>
                <span class="{pnl_cls}">{fmt_pnl(pnl_val)}</span>
            </div>""",
            unsafe_allow_html=True,
        )


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main() -> None:
    inject_css()

    refresh_s = st.sidebar.selectbox("Refresh", [15, 30, 60, 0], format_func=lambda x: f"{x}s" if x else "Off", index=0)
    auto_refresh(refresh_s)

    pnl_data    = fetch_polycop_pnl(POLYCOP_WALLET)
    wallet_conf = load_wallet_conf()

    total_pnl = pnl_data.get("total_pnl")
    n_open    = pnl_data.get("n_open", 0)
    scores    = wallet_conf.get("scores", []) if wallet_conf else []
    n_wallets = sum(1 for s in scores if s.get("confidence", 0) >= 55) if scores else len(WATCHLIST)

    render_header(total_pnl, n_open, n_wallets)

    left, right = st.columns([1.65, 1.0])

    with left:
        with st.container(border=True):
            if pnl_data.get("error"):
                st.warning(f"API: {pnl_data['error']}")
            elif not POLYCOP_WALLET:
                st.info("Configure `POLYCOP_WALLET_ADDRESS` dans .env pour voir ton PnL live.")
            else:
                render_pnl_block(pnl_data)
            st.divider()
            st.markdown("<div class='section-label'>Courbe de PnL</div>", unsafe_allow_html=True)
            render_equity_chart(pnl_data)

    with right:
        with st.container(border=True):
            render_wallets(wallet_conf)

    with st.container(border=True):
        render_positions(pnl_data.get("positions", []))


if __name__ == "__main__":
    main()
