from pathlib import Path

from polybot.research.obsidian_mining import (
    ObsidianVaultReader,
    StrategyExtractor,
    parse_polymarket_threads,
)
from polybot.research.obsidian_mining.edge_synthesis import analyze_threads, render_edge_synthesis_report
from polybot.research.obsidian_mining.strategy_candidate import EdgeFamily
from polybot.research.strategy_registry import StrategyCandidateRegistry


def test_obsidian_strategy_mining_extracts_candidate(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    thread_dir = vault / "Sources" / "Twitter-Threads"
    thread_dir.mkdir(parents=True)
    (thread_dir / "thread.md").write_text(
        """---
type: "twitter-thread"
source: "https://x.com/test/status/1"
author: "test"
status_id: "1"
---
# Twitter Thread - test

## Resume
Polymarket orderbook imbalance keeps appearing before rapid repricing.

## Idees exploitables
Test whether bid-heavy imbalance predicts future mid price movement with sufficient depth.
""",
        encoding="utf-8",
    )

    notes = ObsidianVaultReader(vault).iter_markdown_notes()
    threads = parse_polymarket_threads(notes)
    candidates = StrategyExtractor().extract_from_threads(threads)

    assert len(candidates) >= 2
    assert {candidate.edge_family for candidate in candidates} >= {
        EdgeFamily.ORDERBOOK_IMBALANCE,
        EdgeFamily.LIQUIDITY_VACUUM,
    }


def test_strategy_candidate_registry_status_and_links(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    thread_dir = vault / "Sources" / "Twitter-Threads"
    thread_dir.mkdir(parents=True)
    (thread_dir / "thread.md").write_text(
        """---
type: "twitter-thread"
source: "https://x.com/test/status/1"
---
# Thread

## Resume
Cross-market arbitrage between Polymarket and Kalshi can appear when the net gap covers fees.
The idea requires both legs to have executable depth, controlled slippage, and no unhedged fill.
Backtest the gap after fees and reject any case where one venue cannot fill the hedge.
""",
        encoding="utf-8",
    )
    candidate = StrategyExtractor().extract_from_threads(
        parse_polymarket_threads(ObsidianVaultReader(vault).iter_markdown_notes())
    )[0]
    registry = StrategyCandidateRegistry(tmp_path / "registry.json")

    registry.upsert_candidate(candidate)
    registry.mark_as_promising(candidate.candidate_id, note="Good first hypothesis.")
    registry.link_candidate_to_backtest(candidate.candidate_id, "Backtest-1")

    ranked = registry.rank_candidates()

    assert ranked[0].status.value == "promising"
    assert ranked[0].backtest_results == ["Backtest-1"]


def test_edge_synthesis_flags_placeholders_and_maps_edges(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    thread_dir = vault / "Sources" / "Twitter-Threads"
    thread_dir.mkdir(parents=True)
    (thread_dir / "placeholder.md").write_text(
        """---
type: "twitter-thread"
source: "https://x.com/test/status/1"
---
# Thread

## Resume
Polymarket trading thread. A completer apres extraction du contenu complet du thread.
""",
        encoding="utf-8",
    )
    (thread_dir / "rich.md").write_text(
        """---
type: "twitter-thread"
source: "https://x.com/test/status/2"
author: "test"
---
# Thread

## Resume
Polymarket market making around stable mid prices can work when maker quotes keep inventory balanced.

## Idees exploitables
Backtest two-sided quotes with inventory skew, queue assumptions, visible depth, and adverse selection checks.
""",
        encoding="utf-8",
    )

    threads = parse_polymarket_threads(ObsidianVaultReader(vault).iter_markdown_notes())
    analyses = analyze_threads(threads)
    report = render_edge_synthesis_report(analyses)

    assert {analysis.extraction_status for analysis in analyses} >= {"placeholder", "content_rich"}
    assert "market_making" in report
    assert "Placeholder/raw URL threads" in report
