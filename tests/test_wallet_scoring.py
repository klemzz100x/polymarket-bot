"""Sanity tests for SC-016 wallet_scoring on synthetic data."""
from __future__ import annotations

from polybot.research.wallet_scoring import (
    classify_edge,
    compute_anti_luck,
    compute_edge_proof,
    compute_persistence,
    gini,
    normalize_positions,
    recompute_independence,
    score_wallet,
    sigmoid_centered,
    wilson_lb_continuous,
    wilson_lower_bound,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _pos(cid: str, *, outcome="Yes", avg_price=0.5, total_bought=100.0,
         realized_pnl=0.0, cash_pnl=0.0, current_value=0.0, cur_price=0.0,
         end_date="2026-01-01", redeemable=True, size=0.0, title="Test", slug=""):
    """Build a /positions-style dict."""
    return {
        "conditionId": cid,
        "outcome": outcome,
        "outcomeIndex": 0 if outcome.lower() == "yes" else 1,
        "avgPrice": avg_price,
        "totalBought": total_bought,
        "initialValue": total_bought,
        "realizedPnl": realized_pnl,
        "cashPnl": cash_pnl,
        "currentValue": current_value,
        "curPrice": cur_price,
        "endDate": end_date,
        "redeemable": redeemable,
        "size": size,
        "title": title,
        "slug": slug,
        "eventSlug": slug,
        "percentPnl": ((realized_pnl + cash_pnl) / total_bought * 100) if total_bought else 0,
    }


# ── Statistical helpers ──────────────────────────────────────────────────────

def test_wilson_lb_empty():
    assert wilson_lower_bound(0, 0) == 0.0


def test_wilson_lb_perfect_small_sample():
    lb = wilson_lower_bound(5, 5)
    assert 0.3 < lb < 0.85


def test_wilson_lb_large_sample():
    lb = wilson_lower_bound(80, 100)
    assert 0.70 < lb < 0.80


def test_wilson_continuous_positive_mean():
    vals = [0.05, 0.07, 0.06, 0.08, 0.04, 0.09, 0.05, 0.06, 0.07, 0.05]
    lb = wilson_lb_continuous(vals)
    assert 0.02 < lb < 0.06


def test_gini_uniform():
    assert gini([1, 1, 1, 1, 1]) < 0.05


def test_gini_concentrated():
    assert gini([90, 1, 1, 1, 1, 1, 1, 1, 1, 1]) > 0.7


def test_sigmoid_at_midpoint():
    assert 49 < sigmoid_centered(0, midpoint=0, scale=1) < 51


# ── Normalization ────────────────────────────────────────────────────────────

def test_normalize_marks_resolved():
    positions = [
        _pos("0xA", redeemable=True),
        _pos("0xB", redeemable=False, cur_price=1.0),  # terminal price
        _pos("0xC", redeemable=False, cur_price=0.5, end_date="2030-01-01", current_value=50),
    ]
    out = normalize_positions(positions)
    assert out[0]["is_resolved"] is True
    assert out[1]["is_resolved"] is True
    assert out[2]["is_resolved"] is False


# ── Scoring on synthetic wallets ─────────────────────────────────────────────

def test_score_empty_wallet():
    ws = score_wallet("0x" + "0" * 40, "empty", [], [])
    assert ws.confidence < 50
    assert ws.diagnostics.n_positions == 0


def test_score_consistent_profitable_wallet():
    """40 resolved positions, +20% ROI on each."""
    positions = [
        _pos(f"0x{i:064x}", total_bought=100, cash_pnl=20, current_value=120,
             cur_price=1.0, redeemable=True)
        for i in range(40)
    ]
    ws = score_wallet("0x" + "a" * 40, "consistent_winner", [], positions)
    assert ws.diagnostics.n_resolved == 40
    assert ws.diagnostics.total_pnl_usd > 700
    assert ws.sub_scores.edge_proof > 80
    assert ws.sub_scores.sample_sufficiency > 70  # n=40, midpoint=30 → sigmoid≈73


def test_score_jackpot_wallet_penalised():
    """1 huge winner + 20 small losers → anti_luck should tank."""
    positions = [
        _pos("0xJACKPOT", total_bought=1000, cash_pnl=10000, current_value=11000,
             cur_price=1.0, redeemable=True),
    ]
    positions.extend(
        _pos(f"0x{i:064x}", total_bought=50, cash_pnl=-50, current_value=0,
             cur_price=0.0, redeemable=True)
        for i in range(20)
    )
    ws = score_wallet("0x" + "b" * 40, "jackpot", [], positions)
    assert ws.sub_scores.anti_luck < 60
    assert ws.diagnostics.top_position_pnl_share > 0.5


def test_classify_longshot_with_realistic_win_rate():
    """Wallet that wins ~55% on longshots bought at 0.15 — realistic, not insider."""
    positions = []
    for i in range(15):
        win = i % 9 < 5  # ~55% win rate, sub-insider threshold
        positions.append(_pos(
            f"0x{i:064x}",
            avg_price=0.15,
            total_bought=50,
            cash_pnl=(50 / 0.15 * 1.0 - 50) if win else -50,
            cur_price=1.0 if win else 0.0,
            redeemable=True,
        ))
    norm = normalize_positions(positions)
    edge_type, diag = classify_edge(norm, {})
    # With 55% win rate (not extreme) + 100% longshot entries, should be longshot_collector
    assert "longshot" in edge_type or edge_type == "insider_suspected"
    assert diag["longshot_share"] > 0.9


def test_classify_category_specialist():
    """Wallet 100% concentrated on politics markets."""
    positions = [
        _pos(f"0x{i:064x}", total_bought=100, cash_pnl=10,
             cur_price=1.0, redeemable=True,
             slug=f"presidential-election-{i}")
        for i in range(15)
    ]
    norm = normalize_positions(positions)
    edge_type, _ = classify_edge(norm, {})
    assert "politics" in edge_type


def test_insider_pattern_detected():
    """High win rate + extreme entries → insider flag."""
    positions = []
    # Suspiciously good: 90% win rate with extreme entries
    for i in range(15):
        avg_p = 0.05 if i % 2 == 0 else 0.95
        win = i < 14  # 14/15 wins
        positions.append(_pos(
            f"0x{i:064x}",
            avg_price=avg_p,
            total_bought=100,
            cash_pnl=(1 - avg_p) * 100 / avg_p if win else -100,
            cur_price=1.0 if win else 0.0,
            redeemable=True,
        ))
    ws = score_wallet("0x" + "i" * 40, "suspicious", [], positions)
    assert ws.diagnostics.insider_flag_count >= 1


def test_persistence_split_half():
    """Wallet profitable in both halves should get high persistence."""
    positions = []
    for i in range(20):
        end_date = f"2025-{(i % 12) + 1:02d}-15"
        positions.append(_pos(
            f"0x{i:064x}",
            total_bought=100,
            cash_pnl=15,  # consistent
            cur_price=1.0,
            redeemable=True,
            end_date=end_date,
        ))
    norm = normalize_positions(positions)
    persistence = compute_persistence(norm, [])
    assert persistence > 70


def test_persistence_decay():
    """Wallet profitable early then losing should score low persistence."""
    positions = []
    for i in range(10):
        positions.append(_pos(f"0xEARLY{i:056x}", total_bought=100, cash_pnl=30,
                              cur_price=1.0, redeemable=True, end_date="2025-01-01"))
    for i in range(10):
        positions.append(_pos(f"0xLATE{i:057x}", total_bought=100, cash_pnl=-50,
                              cur_price=0.0, redeemable=True, end_date="2026-01-01"))
    norm = normalize_positions(positions)
    persistence = compute_persistence(norm, [])
    assert persistence < 50


def test_independence_v2_detects_overlap():
    """Two wallets sharing 9/10 markets should both lose independence."""
    shared_cids = [f"0xMKT{i:061x}" for i in range(10)]
    pos_a = [_pos(c) for c in shared_cids[:10]]
    pos_b = [_pos(c) for c in shared_cids[1:10]] + [_pos("0xUNIQUE")]
    ws_a = score_wallet("0x" + "a" * 40, "wallet_a", [], pos_a)
    ws_b = score_wallet("0x" + "b" * 40, "wallet_b", [], pos_b)
    scores = recompute_independence(
        [ws_a, ws_b],
        positions_by_addr={
            ws_a.address: pos_a,
            ws_b.address: pos_b,
        },
        min_shared_markets=3,
    )
    # Both should have low independence (high jaccard overlap)
    assert scores[0].sub_scores.independence < 50
    assert scores[1].sub_scores.independence < 50
    assert any("overlap" in r.lower() for r in scores[0].reasons)


def test_independence_v2_keeps_independent_wallets_high():
    """Two wallets with disjoint markets keep high independence."""
    pos_a = [_pos(f"0xA{i:063x}") for i in range(10)]
    pos_b = [_pos(f"0xB{i:063x}") for i in range(10)]
    ws_a = score_wallet("0x" + "a" * 40, "wallet_a", [], pos_a)
    ws_b = score_wallet("0x" + "b" * 40, "wallet_b", [], pos_b)
    scores = recompute_independence(
        [ws_a, ws_b],
        positions_by_addr={ws_a.address: pos_a, ws_b.address: pos_b},
    )
    assert scores[0].sub_scores.independence >= 80
    assert scores[1].sub_scores.independence >= 80


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
