"""SC-016 — Wallet Confidence Scoring.

Score wallets on short samples (weeks, not months) to detect new edges fast.
Output a 0-100 confidence score with a risk badge that explicitly reflects
sample size, edge significance, luck, and copyability.

Data sources (Polymarket Data API):
    /positions       — aggregated per-market PnL (realizedPnl + cashPnl + totalBought)
                       Primary source for PnL, ROI, win/loss labelling.
    /activity?type=TRADE — individual trade events. Used for timing, hold duration,
                       entry distribution, recent activity signal.

Design philosophy:
    - Never trust raw win rate or headline PnL.
    - Wilson lower bound is the floor for any rate claim.
    - Split-half test forces edge to be persistent, not a single jackpot.
    - Gini of PnL contributions catches "one lucky bet" wallets.
    - Sample sufficiency is a hard penalty, not a vibe.

Output:
    WalletScore dataclass with:
      - confidence (0-100)
      - sub_scores (7 components)
      - edge_type (classification)
      - risk_badge (🟢/🟡/🔴/⚫)
      - diagnostics (raw stats)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import median
from typing import Any


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SubScores:
    edge_proof: float
    sample_sufficiency: float
    persistence: float
    anti_luck: float
    risk_taken: float
    copyability: float
    independence: float

    def weighted(self) -> float:
        """Weighted confidence score (0-100)."""
        return (
            self.edge_proof * 0.25
            + self.sample_sufficiency * 0.15
            + self.persistence * 0.15
            + self.anti_luck * 0.15
            + self.risk_taken * 0.10
            + self.copyability * 0.10
            + self.independence * 0.10
        )


@dataclass(frozen=True)
class Diagnostics:
    n_positions: int
    n_resolved: int
    n_open: int
    n_trades: int
    total_pnl_usd: float
    realized_pnl_usd: float
    total_volume_usd: float
    avg_roi_pct: float
    roi_wilson_lb_pct: float
    win_rate: float
    win_rate_wilson_lb: float
    max_drawdown_pct: float
    top_position_pnl_share: float
    median_hold_hours: float
    avg_entry_price: float
    category_concentration: float
    price_regime_split: dict[str, float]  # {longshot, midprice, favorite}
    main_category: str
    insider_flag_count: int
    last_trade_age_days: float


@dataclass(frozen=True)
class WalletScore:
    address: str
    label: str
    confidence: float
    risk_badge: str
    edge_type: str
    sub_scores: SubScores
    diagnostics: Diagnostics
    reasons: list[str] = field(default_factory=list)


# ── Statistical helpers ──────────────────────────────────────────────────────

def wilson_lower_bound(successes: int, trials: int, z: float = 1.645) -> float:
    """Wilson score lower bound for a binomial proportion (z=1.645 → 90% CI)."""
    if trials <= 0:
        return 0.0
    p = successes / trials
    denom = 1.0 + z * z / trials
    centre = p + z * z / (2 * trials)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * trials)) / trials)
    return max(0.0, (centre - margin) / denom)


def wilson_lb_continuous(values: list[float], z: float = 1.645) -> float:
    """One-sided lower confidence bound on the mean of a sample."""
    n = len(values)
    if n == 0:
        return 0.0
    mean = sum(values) / n
    if n == 1:
        return min(0.0, mean)
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    se = math.sqrt(var / n)
    t_mult = z + (2.0 / math.sqrt(max(n - 1, 1)))
    return mean - t_mult * se


def gini(values: list[float]) -> float:
    """Gini coefficient of non-negative contributions. 0=equal, 1=fully concentrated."""
    positives = [max(0.0, v) for v in values]
    total = sum(positives)
    if total <= 0 or len(positives) < 2:
        return 0.0
    sorted_v = sorted(positives)
    n = len(sorted_v)
    cumulative = sum(i * v for i, v in enumerate(sorted_v, start=1))
    return (2 * cumulative) / (n * total) - (n + 1) / n


def sigmoid_centered(x: float, midpoint: float = 0.0, scale: float = 1.0) -> float:
    """Logistic 0..100 scaled, centred at midpoint."""
    try:
        return 100.0 / (1.0 + math.exp(-(x - midpoint) / max(scale, 1e-9)))
    except OverflowError:
        return 0.0 if x < midpoint else 100.0


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _safe_str(v: Any, default: str = "") -> str:
    return str(v) if v is not None else default


# ── Position normalization ───────────────────────────────────────────────────

def _parse_end_date(s: str) -> float | None:
    """Parse '2026-12-31' or ISO timestamp → epoch seconds."""
    if not s:
        return None
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
        return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
    except (ValueError, TypeError):
        return None


def normalize_positions(positions: list[dict]) -> list[dict]:
    """Convert raw /positions entries into a uniform per-position dict.

    Output fields:
        condition_id, asset, outcome, outcome_index, size, avg_price, cur_price,
        initial_value, current_value, total_bought, realized_pnl, cash_pnl,
        total_pnl, percent_pnl, redeemable, mergeable, end_date_ts, end_date_str,
        is_resolved, market_title, slug, event_slug, negative_risk
    """
    now_ts = datetime.now(timezone.utc).timestamp()
    out: list[dict] = []
    for p in positions:
        if not isinstance(p, dict):
            continue
        cid = _safe_str(p.get("conditionId") or p.get("condition_id"))
        if not cid:
            continue
        end_str = _safe_str(p.get("endDate") or p.get("end_date"))
        end_ts = _parse_end_date(end_str)
        redeemable = bool(p.get("redeemable"))
        realized_pnl = _safe_float(p.get("realizedPnl"))
        cash_pnl = _safe_float(p.get("cashPnl"))
        cur_value = _safe_float(p.get("currentValue"))
        cur_price = _safe_float(p.get("curPrice"))
        size = _safe_float(p.get("size"))
        avg_price = _safe_float(p.get("avgPrice"))
        # A position is resolved if:
        #   - market explicitly redeemable, OR
        #   - market end date has passed AND current value is near 0 (already redeemed), OR
        #   - cur_price is 0 or 1 (terminal), OR
        #   - size is 0 and there's realized PnL (fully exited)
        is_resolved = (
            redeemable
            or (end_ts is not None and end_ts < now_ts)
            or cur_price in (0.0, 1.0)
            or (size <= 0 and abs(realized_pnl) > 0.01)
        )
        total_pnl = realized_pnl + cash_pnl
        total_bought = _safe_float(p.get("totalBought"))

        out.append({
            "condition_id": cid,
            "asset": _safe_str(p.get("asset")),
            "outcome": _safe_str(p.get("outcome")).upper(),
            "outcome_index": int(_safe_float(p.get("outcomeIndex"), 0)),
            "size": size,
            "avg_price": avg_price,
            "cur_price": cur_price,
            "initial_value": _safe_float(p.get("initialValue")),
            "current_value": cur_value,
            "total_bought": total_bought,
            "realized_pnl": realized_pnl,
            "cash_pnl": cash_pnl,
            "total_pnl": total_pnl,
            "percent_pnl": _safe_float(p.get("percentPnl")),
            "redeemable": redeemable,
            "mergeable": bool(p.get("mergeable")),
            "end_date_ts": end_ts,
            "end_date_str": end_str,
            "is_resolved": is_resolved,
            "market_title": _safe_str(p.get("title")),
            "slug": _safe_str(p.get("slug")),
            "event_slug": _safe_str(p.get("eventSlug")),
            "negative_risk": bool(p.get("negativeRisk")),
        })
    return out


def normalize_trades(activity: list[dict]) -> list[dict]:
    """Convert /activity?type=TRADE entries into uniform trade dicts.

    Output fields:
        ts, condition_id, asset, outcome, side, price, size_usd, market_title,
        event_slug
    """
    out: list[dict] = []
    for a in activity:
        if not isinstance(a, dict):
            continue
        a_type = _safe_str(a.get("type")).upper()
        if a_type != "TRADE":
            continue
        out.append({
            "ts": _safe_float(a.get("timestamp")),
            "condition_id": _safe_str(a.get("conditionId")),
            "asset": _safe_str(a.get("asset")),
            "outcome": _safe_str(a.get("outcome")).upper(),
            "side": _safe_str(a.get("side")).upper(),
            "price": _safe_float(a.get("price")),
            "size_usd": _safe_float(a.get("usdcSize") or a.get("size")),
            "market_title": _safe_str(a.get("title")),
            "event_slug": _safe_str(a.get("eventSlug")),
        })
    out.sort(key=lambda x: x["ts"])
    return out


def compute_hold_times(positions: list[dict], trades: list[dict]) -> dict[str, float]:
    """Map condition_id → hold duration in hours (first BUY to last activity or now).

    For positions still open, uses now; for resolved positions, uses end_date or last trade.
    """
    by_market: dict[str, list[dict]] = {}
    for t in trades:
        cid = t["condition_id"]
        if cid:
            by_market.setdefault(cid, []).append(t)

    now_ts = datetime.now(timezone.utc).timestamp()
    out: dict[str, float] = {}
    for pos in positions:
        cid = pos["condition_id"]
        market_trades = by_market.get(cid, [])
        if not market_trades:
            continue
        first_buy = next((t for t in market_trades if t["side"] == "BUY"), market_trades[0])
        start = first_buy["ts"]
        if pos["is_resolved"]:
            # End = last trade ts OR end_date (whichever is earlier and non-zero)
            last_trade_ts = market_trades[-1]["ts"]
            end = pos.get("end_date_ts") or last_trade_ts
            if last_trade_ts > 0 and last_trade_ts < end:
                end = last_trade_ts
        else:
            end = now_ts
        hold_hours = max(0.0, (end - start) / 3600)
        out[cid] = hold_hours
    return out


# ── Sub-score computations ───────────────────────────────────────────────────

def compute_edge_proof(positions: list[dict]) -> float:
    """Wilson lower bound of per-position ROI."""
    rois = []
    for p in positions:
        cost = p["total_bought"] or p["initial_value"]
        if cost > 0:
            rois.append(p["total_pnl"] / cost)
    if not rois:
        return 0.0
    roi_lb = wilson_lb_continuous(rois)
    return sigmoid_centered(roi_lb * 100, midpoint=2.0, scale=4.0)


def compute_sample_sufficiency(n_resolved: int) -> float:
    """Sigmoid centred at 30 resolved positions."""
    return sigmoid_centered(n_resolved, midpoint=30.0, scale=10.0)


def compute_persistence(positions: list[dict], trades: list[dict]) -> float:
    """Split-half ROI test on resolved positions ordered by their first trade ts."""
    resolved = [p for p in positions if p["is_resolved"]]
    if len(resolved) < 6:
        return 50.0

    # Order by first trade ts (use end_date as fallback)
    by_market_first_ts: dict[str, float] = {}
    for t in trades:
        cid = t["condition_id"]
        if cid and (cid not in by_market_first_ts or t["ts"] < by_market_first_ts[cid]):
            by_market_first_ts[cid] = t["ts"]

    def sort_key(p: dict) -> float:
        return by_market_first_ts.get(p["condition_id"], p.get("end_date_ts") or 0)

    sorted_p = sorted(resolved, key=sort_key)
    mid = len(sorted_p) // 2
    h1, h2 = sorted_p[:mid], sorted_p[mid:]

    def roi_of(ps: list[dict]) -> float:
        cost = sum(p["total_bought"] or p["initial_value"] for p in ps)
        pnl = sum(p["total_pnl"] for p in ps)
        return pnl / cost if cost > 0 else 0.0

    r1, r2 = roi_of(h1), roi_of(h2)
    if r1 <= 0 and r2 <= 0:
        return 0.0
    if r1 <= 0 or r2 <= 0:
        return 25.0
    ratio = min(r1, r2) / max(r1, r2)
    bonus = 10.0 if r2 >= r1 else 0.0
    return min(100.0, ratio * 90.0 + bonus)


def compute_anti_luck(positions: list[dict]) -> float:
    """Inverse Gini of positive-PnL contributions across positions."""
    pnls = [p["total_pnl"] for p in positions if p["total_pnl"] > 0]
    if len(pnls) < 3:
        return 30.0
    g = gini(pnls)
    return max(0.0, min(100.0, (1.0 - g) * 100.0))


def compute_risk_taken(positions: list[dict]) -> float:
    """Penalize high drawdown or high position concentration."""
    if not positions:
        return 50.0

    # Equity curve from resolved positions (ordered by end_date)
    resolved = sorted(
        [p for p in positions if p["is_resolved"]],
        key=lambda p: p.get("end_date_ts") or 0,
    )
    equity = peak = max_dd = 0.0
    for p in resolved:
        equity += p["total_pnl"]
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak)

    # Open position concentration
    open_pos = [p for p in positions if not p["is_resolved"]]
    open_values = sorted([p["current_value"] for p in open_pos if p["current_value"] > 0], reverse=True)
    top_share = 0.0
    if open_values and sum(open_values) > 0:
        top_share = open_values[0] / sum(open_values)

    dd_score = max(0.0, 100.0 - max_dd * 200.0)
    conc_score = max(0.0, 100.0 - max(0.0, top_share - 0.3) * 200.0)
    return 0.6 * dd_score + 0.4 * conc_score


def compute_copyability(hold_times: dict[str, float]) -> float:
    """Score by median hold time. PolyCop reaction is ~2s, so anything >5min is copyable."""
    holds = [h for h in hold_times.values() if h > 0]
    if not holds:
        return 30.0
    med_hold = median(holds)
    # log scale: 1min ≈ 30, 1h ≈ 70, 1d ≈ 90
    return sigmoid_centered(math.log10(max(med_hold, 0.001) * 60 + 1), midpoint=1.5, scale=0.6)


def compute_independence(_address: str, _positions: list[dict]) -> float:
    """v1 placeholder. v2: cross-wallet co-occurrence in same markets/blocks."""
    return 70.0


# ── Edge classification ──────────────────────────────────────────────────────

def classify_edge(positions: list[dict], hold_times: dict[str, float]) -> tuple[str, dict]:
    if not positions:
        return "unknown", {}

    entry_prices = [p["avg_price"] for p in positions if p["avg_price"] > 0]
    if not entry_prices:
        return "unknown", {}

    longshot = sum(1 for p in entry_prices if p < 0.20) / len(entry_prices)
    midprice = sum(1 for p in entry_prices if 0.35 <= p <= 0.65) / len(entry_prices)
    favorite = sum(1 for p in entry_prices if p > 0.80) / len(entry_prices)

    # Category from event_slug prefix (politics, sports, crypto, weather, etc.)
    cats: dict[str, int] = {}
    for p in positions:
        slug = p.get("event_slug", "") or p.get("slug", "")
        cat = _infer_category(slug, p.get("market_title", ""))
        cats[cat] = cats.get(cat, 0) + 1
    main_cat = max(cats.items(), key=lambda kv: kv[1])[0] if cats else "unknown"
    cat_share = cats.get(main_cat, 0) / len(positions) if positions else 0

    holds = [h for h in hold_times.values() if h > 0]
    med_hold = median(holds) if holds else 0

    # Insider heuristic on resolved positions
    resolved = [p for p in positions if p["is_resolved"]]
    wins = sum(1 for p in resolved if p["total_pnl"] > 0)
    win_rate = wins / len(resolved) if resolved else 0
    insider_flags = 0
    if win_rate > 0.85 and len(resolved) >= 10:
        insider_flags += 1
    pnls = [p["total_pnl"] for p in positions if p["total_pnl"] > 0]
    if pnls and gini(pnls) < 0.30 and win_rate > 0.75:
        insider_flags += 1
    extreme_entries = sum(1 for p in entry_prices if p < 0.10 or p > 0.90) / len(entry_prices)
    if extreme_entries > 0.40 and win_rate > 0.70:
        insider_flags += 2

    diagnostics = {
        "longshot_share": round(longshot, 3),
        "midprice_share": round(midprice, 3),
        "favorite_share": round(favorite, 3),
        "main_category": main_cat,
        "category_concentration": round(cat_share, 3),
        "median_hold_hours": round(med_hold, 2),
        "insider_flags": insider_flags,
        "resolved_win_rate": round(win_rate, 3),
    }

    if insider_flags >= 3:
        return "insider_suspected", diagnostics
    if cat_share > 0.65 and main_cat not in {"", "unknown", "other"}:
        return f"category_specialist:{main_cat}", diagnostics
    if longshot > 0.50:
        return "longshot_collector" if win_rate >= 0.40 else "longshot_fader", diagnostics
    if favorite > 0.50:
        return "favorite_collector", diagnostics
    if midprice > 0.55 and med_hold < 6:
        return "midprice_market_maker", diagnostics
    if med_hold < 0.5:
        return "hft_uncopyable", diagnostics
    return "general_trader", diagnostics


def _infer_category(slug: str, title: str) -> str:
    """Lightweight category inference from market slug/title."""
    s = (slug + " " + title).lower()
    if any(k in s for k in ("election", "president", "congress", "senate", "trump", "biden",
                            "vote", "primary", "vance", "harris")):
        return "politics"
    if any(k in s for k in ("nba", "nfl", "mlb", "nhl", "soccer", "premier", "champions",
                            "fc-", "match", "game", "vs-", "champion")):
        return "sports"
    if any(k in s for k in ("bitcoin", "btc", "ethereum", "eth", "crypto", "solana", "sol-",
                            "doge", "xrp")):
        return "crypto"
    if any(k in s for k in ("temperature", "rain", "snow", "hurricane", "weather")):
        return "weather"
    if any(k in s for k in ("ai", "openai", "anthropic", "model", "chatgpt", "gpt-")):
        return "ai_tech"
    if any(k in s for k in ("war", "ukraine", "russia", "china", "taiwan", "israel", "gaza")):
        return "geopolitics"
    if any(k in s for k in ("fed", "rate", "inflation", "cpi", "gdp", "recession", "earnings")):
        return "macro"
    return "other"


# ── Main scoring entry point ─────────────────────────────────────────────────

def score_wallet(
    address: str,
    label: str,
    activity: list[dict],
    positions: list[dict],
) -> WalletScore:
    """Compute a complete WalletScore.

    Args:
        activity: raw rows from /activity (filter to TRADE recommended)
        positions: raw rows from /positions
    """
    norm_positions = normalize_positions(positions)
    norm_trades = normalize_trades(activity)
    hold_times = compute_hold_times(norm_positions, norm_trades)

    resolved = [p for p in norm_positions if p["is_resolved"]]
    open_pos = [p for p in norm_positions if not p["is_resolved"]]

    sub = SubScores(
        edge_proof=compute_edge_proof(norm_positions),
        sample_sufficiency=compute_sample_sufficiency(len(resolved)),
        persistence=compute_persistence(norm_positions, norm_trades),
        anti_luck=compute_anti_luck(norm_positions),
        risk_taken=compute_risk_taken(norm_positions),
        copyability=compute_copyability(hold_times),
        independence=compute_independence(address, norm_positions),
    )
    confidence = sub.weighted()
    edge_type, edge_diag = classify_edge(norm_positions, hold_times)

    # Diagnostics
    pnl_total = sum(p["total_pnl"] for p in norm_positions)
    pnl_realized = sum(p["realized_pnl"] for p in norm_positions)
    volume_total = sum(p["total_bought"] for p in norm_positions)

    rois = [p["total_pnl"] / p["total_bought"] for p in norm_positions if p["total_bought"] > 0]
    avg_roi = sum(rois) / len(rois) * 100 if rois else 0.0
    roi_lb = wilson_lb_continuous(rois) * 100 if rois else 0.0

    wins = sum(1 for p in resolved if p["total_pnl"] > 0)
    win_rate = wins / len(resolved) if resolved else 0.0
    win_rate_lb = wilson_lower_bound(wins, len(resolved))

    pnls = [p["total_pnl"] for p in norm_positions]
    top_share = max((abs(x) for x in pnls), default=0) / max(abs(pnl_total), 1.0) if pnls else 0.0

    holds = [h for h in hold_times.values() if h > 0]
    med_hold = median(holds) if holds else 0.0

    entry_prices = [p["avg_price"] for p in norm_positions if p["avg_price"] > 0]
    avg_entry = sum(entry_prices) / len(entry_prices) if entry_prices else 0.0

    sorted_resolved = sorted(resolved, key=lambda p: p.get("end_date_ts") or 0)
    equity = peak = max_dd = 0.0
    for p in sorted_resolved:
        equity += p["total_pnl"]
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak)

    last_trade_age_days = 999.0
    if norm_trades:
        last_ts = max(t["ts"] for t in norm_trades)
        if last_ts > 0:
            last_trade_age_days = max(0.0, (datetime.now(timezone.utc).timestamp() - last_ts) / 86400)

    diag = Diagnostics(
        n_positions=len(norm_positions),
        n_resolved=len(resolved),
        n_open=len(open_pos),
        n_trades=len(norm_trades),
        total_pnl_usd=round(pnl_total, 2),
        realized_pnl_usd=round(pnl_realized, 2),
        total_volume_usd=round(volume_total, 2),
        avg_roi_pct=round(avg_roi, 2),
        roi_wilson_lb_pct=round(roi_lb, 2),
        win_rate=round(win_rate, 3),
        win_rate_wilson_lb=round(win_rate_lb, 3),
        max_drawdown_pct=round(max_dd * 100, 1),
        top_position_pnl_share=round(top_share, 3),
        median_hold_hours=round(med_hold, 2),
        avg_entry_price=round(avg_entry, 3),
        category_concentration=edge_diag.get("category_concentration", 0.0),
        price_regime_split={
            "longshot": edge_diag.get("longshot_share", 0.0),
            "midprice": edge_diag.get("midprice_share", 0.0),
            "favorite": edge_diag.get("favorite_share", 0.0),
        },
        main_category=edge_diag.get("main_category", "unknown"),
        insider_flag_count=edge_diag.get("insider_flags", 0),
        last_trade_age_days=round(last_trade_age_days, 1),
    )

    # Risk badge
    reasons: list[str] = []
    if diag.insider_flag_count >= 3:
        badge = "⚫ BLACK"
        reasons.append(f"Insider pattern suspected ({diag.insider_flag_count} flags)")
    elif diag.n_resolved < 10:
        badge = "🔴 RED"
        reasons.append(f"Insufficient sample: only {diag.n_resolved} resolved positions")
    elif confidence < 50:
        badge = "🔴 RED"
        reasons.append(f"Confidence {confidence:.0f}/100 below threshold")
    elif confidence >= 75 and diag.n_resolved >= 40 and sub.persistence >= 50:
        badge = "🟢 GREEN"
        reasons.append("Strong edge with persistence and sample")
    else:
        badge = "🟡 YELLOW"
        if sub.persistence < 50:
            reasons.append("Edge not yet persistent across split-halves")
        if diag.n_resolved < 40:
            reasons.append(f"Limited sample ({diag.n_resolved} resolved)")
        if sub.anti_luck < 50:
            reasons.append(f"PnL concentrated (top position = {diag.top_position_pnl_share:.0%})")

    if sub.copyability < 30:
        reasons.append(f"Hold time {diag.median_hold_hours:.1f}h — too fast to copy")
    if sub.edge_proof < 40:
        reasons.append(f"ROI lower bound {diag.roi_wilson_lb_pct:.1f}% — edge not proven")
    if diag.last_trade_age_days > 14:
        reasons.append(f"Inactive {diag.last_trade_age_days:.0f}d — may have stopped")

    return WalletScore(
        address=address,
        label=label,
        confidence=round(confidence, 1),
        risk_badge=badge,
        edge_type=edge_type,
        sub_scores=sub,
        diagnostics=diag,
        reasons=reasons,
    )


def recompute_independence(
    scores: list[WalletScore],
    positions_by_addr: dict[str, list[dict]],
    *,
    min_shared_markets: int = 5,
) -> list[WalletScore]:
    """Post-process: compute jaccard overlap between wallets and update independence.

    Two wallets that hold positions in >80% of the same markets are likely
    one trader operating multiple wallets (or coordinated farms).

    Score logic:
        - For each wallet, find its max jaccard with any other wallet
        - independence = (1 - max_jaccard) * 100
        - Floor 20 (some overlap is normal even among independent sharps)
    """
    # Build market sets per wallet
    market_sets: dict[str, set[str]] = {}
    for addr, positions in positions_by_addr.items():
        cids = {p.get("conditionId") for p in positions if p.get("conditionId")}
        if len(cids) >= 3:  # ignore wallets with too few markets
            market_sets[addr] = cids

    # Compute pairwise jaccard
    max_jaccard: dict[str, tuple[float, str]] = {}
    addrs = list(market_sets.keys())
    for i, a in enumerate(addrs):
        sa = market_sets[a]
        best = (0.0, "")
        for b in addrs:
            if a == b:
                continue
            sb = market_sets[b]
            shared = len(sa & sb)
            if shared < min_shared_markets:
                continue
            union = len(sa | sb)
            j = shared / union if union else 0.0
            if j > best[0]:
                best = (j, b)
        max_jaccard[a] = best

    # Rebuild scores with updated independence + confidence
    out: list[WalletScore] = []
    for ws in scores:
        j, partner = max_jaccard.get(ws.address, (0.0, ""))
        new_indep = max(20.0, (1.0 - j) * 100.0)
        new_sub = SubScores(
            edge_proof=ws.sub_scores.edge_proof,
            sample_sufficiency=ws.sub_scores.sample_sufficiency,
            persistence=ws.sub_scores.persistence,
            anti_luck=ws.sub_scores.anti_luck,
            risk_taken=ws.sub_scores.risk_taken,
            copyability=ws.sub_scores.copyability,
            independence=new_indep,
        )
        new_conf = new_sub.weighted()
        new_reasons = list(ws.reasons)
        if j > 0.5 and partner:
            new_reasons.append(
                f"Heavy market overlap (jaccard {j:.0%} with {partner[:10]}…) — likely linked wallet"
            )
        out.append(WalletScore(
            address=ws.address,
            label=ws.label,
            confidence=round(new_conf, 1),
            risk_badge=ws.risk_badge,  # Badge logic unchanged for now
            edge_type=ws.edge_type,
            sub_scores=new_sub,
            diagnostics=ws.diagnostics,
            reasons=new_reasons,
        ))
    return out


def score_to_dict(ws: WalletScore) -> dict:
    return {
        "address": ws.address,
        "label": ws.label,
        "confidence": ws.confidence,
        "risk_badge": ws.risk_badge,
        "edge_type": ws.edge_type,
        "sub_scores": {
            "edge_proof": round(ws.sub_scores.edge_proof, 1),
            "sample_sufficiency": round(ws.sub_scores.sample_sufficiency, 1),
            "persistence": round(ws.sub_scores.persistence, 1),
            "anti_luck": round(ws.sub_scores.anti_luck, 1),
            "risk_taken": round(ws.sub_scores.risk_taken, 1),
            "copyability": round(ws.sub_scores.copyability, 1),
            "independence": round(ws.sub_scores.independence, 1),
        },
        "diagnostics": {
            "n_positions": ws.diagnostics.n_positions,
            "n_resolved": ws.diagnostics.n_resolved,
            "n_open": ws.diagnostics.n_open,
            "n_trades": ws.diagnostics.n_trades,
            "total_pnl_usd": ws.diagnostics.total_pnl_usd,
            "realized_pnl_usd": ws.diagnostics.realized_pnl_usd,
            "total_volume_usd": ws.diagnostics.total_volume_usd,
            "avg_roi_pct": ws.diagnostics.avg_roi_pct,
            "roi_wilson_lb_pct": ws.diagnostics.roi_wilson_lb_pct,
            "win_rate": ws.diagnostics.win_rate,
            "win_rate_wilson_lb": ws.diagnostics.win_rate_wilson_lb,
            "max_drawdown_pct": ws.diagnostics.max_drawdown_pct,
            "top_position_pnl_share": ws.diagnostics.top_position_pnl_share,
            "median_hold_hours": ws.diagnostics.median_hold_hours,
            "avg_entry_price": ws.diagnostics.avg_entry_price,
            "main_category": ws.diagnostics.main_category,
            "category_concentration": ws.diagnostics.category_concentration,
            "price_regime_split": ws.diagnostics.price_regime_split,
            "insider_flag_count": ws.diagnostics.insider_flag_count,
            "last_trade_age_days": ws.diagnostics.last_trade_age_days,
        },
        "reasons": ws.reasons,
    }
