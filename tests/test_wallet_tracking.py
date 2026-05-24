"""Tests for SC-016 wallet_tracking diffs."""
from __future__ import annotations

from polybot.research.wallet_tracking import diff_scans


def _score(addr, label, conf, badge, edge="general_trader", last_age_days=1, n_resolved=20):
    return {
        "address": addr,
        "label": label,
        "confidence": conf,
        "risk_badge": badge,
        "edge_type": edge,
        "diagnostics": {
            "n_resolved": n_resolved,
            "last_trade_age_days": last_age_days,
        },
    }


def test_diff_detects_new_wallet():
    current = {"scan_ts": "t2", "scores": [
        _score("0xA", "alice", 65, "🟡 YELLOW"),
        _score("0xB", "bob", 80, "🟢 GREEN"),
    ]}
    previous = {"scan_ts": "t1", "scores": [
        _score("0xA", "alice", 65, "🟡 YELLOW"),
    ]}
    report = diff_scans(current, previous)
    assert len(report.new_wallets) == 1
    assert report.new_wallets[0].address == "0xB"


def test_diff_detects_promotion():
    current = {"scan_ts": "t2", "scores": [
        _score("0xA", "alice", 80, "🟢 GREEN"),
    ]}
    previous = {"scan_ts": "t1", "scores": [
        _score("0xA", "alice", 65, "🟡 YELLOW"),
    ]}
    report = diff_scans(current, previous)
    assert len(report.promoted) == 1
    assert report.promoted[0].address == "0xA"


def test_diff_detects_demotion():
    current = {"scan_ts": "t2", "scores": [
        _score("0xA", "alice", 45, "🔴 RED"),
    ]}
    previous = {"scan_ts": "t1", "scores": [
        _score("0xA", "alice", 65, "🟡 YELLOW"),
    ]}
    report = diff_scans(current, previous)
    assert len(report.demoted) == 1


def test_diff_detects_decay_same_badge():
    current = {"scan_ts": "t2", "scores": [
        _score("0xA", "alice", 52, "🟡 YELLOW"),
    ]}
    previous = {"scan_ts": "t1", "scores": [
        _score("0xA", "alice", 65, "🟡 YELLOW"),
    ]}
    report = diff_scans(current, previous)
    assert len(report.decaying) == 1
    assert report.decaying[0].delta_confidence < -10


def test_diff_detects_newly_inactive():
    current = {"scan_ts": "t2", "scores": [
        _score("0xA", "alice", 65, "🟡 YELLOW", last_age_days=20),
    ]}
    previous = {"scan_ts": "t1", "scores": [
        _score("0xA", "alice", 65, "🟡 YELLOW", last_age_days=2),
    ]}
    report = diff_scans(current, previous)
    assert len(report.newly_inactive) == 1


def test_diff_no_previous():
    current = {"scan_ts": "t1", "scores": [_score("0xA", "alice", 65, "🟡 YELLOW")]}
    report = diff_scans(current, None)
    assert report.prev_scan_ts is None
    assert report.n_previous == 0
