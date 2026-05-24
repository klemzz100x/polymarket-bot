"""
Tests for run_wallet_watchdog.py — classification, auto-copy filters, sizing.

Run: PYTHONPATH=src python -m pytest tests/test_watchdog.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_wallet_watchdog import (
    _classify,
    _compute_copy_size_pct,
    _is_safe_for_autocopy,
    _queue_for_polycop,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _wallet(
    conf: float = 72,
    badge: str = "🟢 GREEN",
    edge_proof: float = 70,
    n_resolved: int = 50,
    last_trade_age_days: float = 3.0,
    anti_luck: float = 60,
    persistence: float = 60,
    total_pnl_usd: float = 1200.0,
    insider_flag_count: int = 0,
    copyability: float = 65,
    address: str = "0xABC",
    label: str = "test_wallet",
    edge_type: str = "category_specialist:crypto",
) -> dict:
    return {
        "address": address,
        "label": label,
        "confidence": conf,
        "risk_badge": badge,
        "edge_type": edge_type,
        "sub_scores": {
            "edge_proof": edge_proof,
            "persistence": persistence,
            "anti_luck": anti_luck,
            "copyability": copyability,
            "sample_sufficiency": 50,
            "risk_taken": 50,
            "independence": 50,
        },
        "diagnostics": {
            "n_resolved": n_resolved,
            "last_trade_age_days": last_trade_age_days,
            "insider_flag_count": insider_flag_count,
            "total_pnl_usd": total_pnl_usd,
            "win_rate_wilson_lb": 0.62,
            "n_positions": n_resolved + 5,
            "n_open": 3,
        },
    }


# ── _classify ─────────────────────────────────────────────────────────────────

class TestClassify:
    DEFAULTS = dict(min_confidence=55, edge_threshold=65, max_trades=20)

    def test_qualified_above_threshold(self):
        assert _classify(_wallet(conf=60), **self.DEFAULTS) == "qualified"

    def test_qualified_at_threshold(self):
        assert _classify(_wallet(conf=55), **self.DEFAULTS) == "qualified"

    def test_qualified_high_conf(self):
        assert _classify(_wallet(conf=90), **self.DEFAULTS) == "qualified"

    def test_emerging_low_conf_high_edge(self):
        ws = _wallet(conf=40, edge_proof=68, n_resolved=15)
        assert _classify(ws, **self.DEFAULTS) == "emerging"

    def test_emerging_at_edge_threshold(self):
        ws = _wallet(conf=40, edge_proof=65, n_resolved=20)
        assert _classify(ws, **self.DEFAULTS) == "emerging"

    def test_emerging_too_many_trades(self):
        # n_resolved > max_trades → not emerging
        ws = _wallet(conf=40, edge_proof=80, n_resolved=21)
        assert _classify(ws, **self.DEFAULTS) is None

    def test_emerging_below_edge_threshold(self):
        ws = _wallet(conf=40, edge_proof=60, n_resolved=10)
        assert _classify(ws, **self.DEFAULTS) is None

    def test_emerging_conf_too_low(self):
        # conf < 30 → no signal at all
        ws = _wallet(conf=25, edge_proof=80, n_resolved=5)
        assert _classify(ws, **self.DEFAULTS) is None

    def test_skip_black_badge(self):
        ws = _wallet(conf=90, badge="⚫ BLACK")
        assert _classify(ws, **self.DEFAULTS) is None

    def test_skip_insider_flag(self):
        ws = _wallet(conf=80, insider_flag_count=1)
        assert _classify(ws, **self.DEFAULTS) is None

    def test_skip_red_below_threshold(self):
        ws = _wallet(conf=40, badge="🔴 RED", edge_proof=50)
        assert _classify(ws, **self.DEFAULTS) is None


# ── _is_safe_for_autocopy ─────────────────────────────────────────────────────

class TestIsAutocopySafe:
    def test_all_pass(self):
        ok, reason = _is_safe_for_autocopy(_wallet())
        assert ok, reason

    def test_fail_not_green(self):
        ok, _ = _is_safe_for_autocopy(_wallet(badge="🟡 YELLOW"))
        assert not ok

    def test_fail_red_badge(self):
        ok, _ = _is_safe_for_autocopy(_wallet(badge="🔴 RED"))
        assert not ok

    def test_fail_confidence_below_70(self):
        ok, reason = _is_safe_for_autocopy(_wallet(conf=69))
        assert not ok
        assert "conf" in reason

    def test_fail_confidence_exactly_70_passes(self):
        ok, _ = _is_safe_for_autocopy(_wallet(conf=70))
        assert ok

    def test_fail_insider_flag(self):
        ok, reason = _is_safe_for_autocopy(_wallet(insider_flag_count=1))
        assert not ok
        assert "insider" in reason

    def test_fail_too_few_trades(self):
        ok, reason = _is_safe_for_autocopy(_wallet(n_resolved=24))
        assert not ok
        assert "n_resolved" in reason

    def test_pass_exactly_25_trades(self):
        ok, _ = _is_safe_for_autocopy(_wallet(n_resolved=25))
        assert ok

    def test_fail_dormant(self):
        ok, reason = _is_safe_for_autocopy(_wallet(last_trade_age_days=15))
        assert not ok
        assert "dormant" in reason

    def test_pass_exactly_14_days(self):
        ok, _ = _is_safe_for_autocopy(_wallet(last_trade_age_days=14))
        assert ok

    def test_fail_low_anti_luck(self):
        ok, reason = _is_safe_for_autocopy(_wallet(anti_luck=49))
        assert not ok
        assert "anti_luck" in reason

    def test_fail_low_persistence(self):
        ok, reason = _is_safe_for_autocopy(_wallet(persistence=49))
        assert not ok
        assert "persistence" in reason

    def test_fail_low_pnl(self):
        ok, reason = _is_safe_for_autocopy(_wallet(total_pnl_usd=499))
        assert not ok
        assert "pnl" in reason.lower()

    def test_pass_exactly_500_pnl(self):
        ok, _ = _is_safe_for_autocopy(_wallet(total_pnl_usd=500))
        assert ok

    def test_custom_min_confidence(self):
        ok, _ = _is_safe_for_autocopy(_wallet(conf=80), autocopy_min_confidence=80)
        assert ok
        ok, _ = _is_safe_for_autocopy(_wallet(conf=79), autocopy_min_confidence=80)
        assert not ok


# ── _compute_copy_size_pct ────────────────────────────────────────────────────

class TestCopySizePct:
    def test_min_conf_70_no_bonuses(self):
        pct = _compute_copy_size_pct(_wallet(conf=70, persistence=60, anti_luck=60))
        assert pct == 0.5

    def test_max_conf_100_no_bonuses(self):
        pct = _compute_copy_size_pct(_wallet(conf=100, persistence=60, anti_luck=60))
        assert pct == 2.0

    def test_mid_conf_85_no_bonuses(self):
        pct = _compute_copy_size_pct(_wallet(conf=85, persistence=60, anti_luck=60))
        assert abs(pct - 1.25) < 0.05

    def test_persistence_bonus(self):
        base = _compute_copy_size_pct(_wallet(conf=70, persistence=60, anti_luck=60))
        with_bonus = _compute_copy_size_pct(_wallet(conf=70, persistence=70, anti_luck=60))
        assert with_bonus == base + 0.25

    def test_anti_luck_bonus(self):
        base = _compute_copy_size_pct(_wallet(conf=70, persistence=60, anti_luck=60))
        with_bonus = _compute_copy_size_pct(_wallet(conf=70, persistence=60, anti_luck=70))
        assert with_bonus == base + 0.25

    def test_both_bonuses_capped_at_2(self):
        pct = _compute_copy_size_pct(_wallet(conf=100, persistence=80, anti_luck=80))
        assert pct == 2.0

    def test_result_always_between_05_and_2(self):
        for conf in range(70, 101, 5):
            for persist in [50, 70, 90]:
                for luck in [50, 70, 90]:
                    pct = _compute_copy_size_pct(_wallet(conf=conf, persistence=persist, anti_luck=luck))
                    assert 0.5 <= pct <= 2.0, f"out of range: conf={conf} pct={pct}"


# ── _queue_for_polycop ────────────────────────────────────────────────────────

class TestQueueForPolycop:
    def test_adds_item(self, tmp_path, monkeypatch):
        import run_wallet_watchdog as ww
        monkeypatch.setattr(ww, "POLYCOP_QUEUE", tmp_path / "queue.json")
        ws = _wallet(address="0x111", label="wallet_a", conf=75)
        _queue_for_polycop(ws)

        queue = json.loads((tmp_path / "queue.json").read_text())
        assert len(queue) == 1
        item = queue[0]
        assert item["address"] == "0x111"
        assert item["label"] == "wallet_a"
        assert item["status"] == "pending"
        assert 0.5 <= item["size_pct"] <= 2.0

    def test_idempotent(self, tmp_path, monkeypatch):
        import run_wallet_watchdog as ww
        monkeypatch.setattr(ww, "POLYCOP_QUEUE", tmp_path / "queue.json")
        ws = _wallet(address="0x222")
        _queue_for_polycop(ws)
        _queue_for_polycop(ws)  # second call should not add duplicate

        queue = json.loads((tmp_path / "queue.json").read_text())
        assert len(queue) == 1

    def test_multiple_wallets(self, tmp_path, monkeypatch):
        import run_wallet_watchdog as ww
        monkeypatch.setattr(ww, "POLYCOP_QUEUE", tmp_path / "queue.json")
        _queue_for_polycop(_wallet(address="0xAAA", label="alpha"))
        _queue_for_polycop(_wallet(address="0xBBB", label="beta"))

        queue = json.loads((tmp_path / "queue.json").read_text())
        assert len(queue) == 2
        assert {i["address"] for i in queue} == {"0xAAA", "0xBBB"}

    def test_size_pct_stored(self, tmp_path, monkeypatch):
        import run_wallet_watchdog as ww
        monkeypatch.setattr(ww, "POLYCOP_QUEUE", tmp_path / "queue.json")
        ws = _wallet(address="0xCCC", conf=85, persistence=75, anti_luck=75)
        _queue_for_polycop(ws)

        queue = json.loads((tmp_path / "queue.json").read_text())
        expected = _compute_copy_size_pct(ws)
        assert queue[0]["size_pct"] == expected
