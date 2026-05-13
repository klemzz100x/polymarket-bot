from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from polybot.core.compat import UTC

from polybot.research.obsidian_mining.strategy_candidate import EdgeFamily, StrategyCandidate
from polybot.research.obsidian_mining.strategy_extractor import EDGE_KEYWORDS, StrategyExtractor
from polybot.research.obsidian_mining.thread_parser import TwitterThreadNote


PLACEHOLDER_MARKERS = (
    "a completer apres extraction",
    "a extraire",
    "source non auditee",
    "recherche a qualifier",
    "inboxed for research mining",
)

BOILERPLATE_MARKERS = (
    "extract actionable strategy ideas",
    "classify possible edge families",
    "link each idea to measurable signals",
    "identify required polymarket data",
    "decide whether this can become a strategy candidate",
    "edge families to check",
    "strategy candidate hooks",
    "verifier si le thread contient une hypothese testable",
    "transformer toute strategie mentionnee en spec de backtest",
    "classer les idees entre execution, pricing, market making, arbitrage, data ou tooling",
    "extraire le contenu via workflow n8n",
    "faire une note strategie separee",
    "lier les hypotheses a un backtest reproductible",
)


@dataclass(frozen=True, slots=True)
class ThreadEdgeAnalysis:
    source_title: str
    source_path: str
    source_url: str | None
    author: str | None
    status_id: str | None
    extraction_status: str
    evidence_quality: str
    text_chars: int
    edge_families: list[EdgeFamily]
    candidates: list[StrategyCandidate] = field(default_factory=list)
    missing_work: list[str] = field(default_factory=list)


def analyze_threads(threads: list[TwitterThreadNote]) -> list[ThreadEdgeAnalysis]:
    extractor = StrategyExtractor()
    analyses: list[ThreadEdgeAnalysis] = []
    for thread in threads:
        clean_text = _clean_research_text(thread.text)
        status = classify_extraction_status(thread.text, clean_text)
        candidates = extractor.extract_from_thread(thread) if status != "placeholder" else []
        families = sorted({candidate.edge_family for candidate in candidates}, key=lambda family: family.value)
        if not families:
            families = detect_families_from_keywords(clean_text)
        analyses.append(
            ThreadEdgeAnalysis(
                source_title=thread.note.title,
                source_path=thread.note.relative_path,
                source_url=thread.source_url,
                author=thread.author,
                status_id=thread.status_id,
                extraction_status=status,
                evidence_quality=evidence_quality(status=status, text=clean_text, candidates=candidates),
                text_chars=len(clean_text),
                edge_families=families,
                candidates=candidates,
                missing_work=missing_work(status=status, families=families),
            )
        )
    return analyses


def classify_extraction_status(raw_text: str, clean_text: str) -> str:
    lowered = raw_text.lower()
    clean_lowered = clean_text.lower()
    if any(marker in lowered for marker in PLACEHOLDER_MARKERS) and len(clean_text) < 500:
        return "placeholder"
    if len(clean_text) < 180:
        return "raw_url_only"
    if any(marker in lowered for marker in PLACEHOLDER_MARKERS):
        return "needs_extraction"
    if "http" in clean_lowered and len(clean_text) < 500:
        return "needs_extraction"
    return "content_rich"


def detect_families_from_keywords(text: str) -> list[EdgeFamily]:
    lowered = text.lower()
    scores: list[tuple[int, EdgeFamily]] = []
    for family, keywords in EDGE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score:
            scores.append((score, family))
    return [family for _score, family in sorted(scores, key=lambda item: (-item[0], item[1].value))]


def evidence_quality(*, status: str, text: str, candidates: list[StrategyCandidate]) -> str:
    if status in {"placeholder", "raw_url_only"}:
        return "insufficient"
    if not candidates:
        return "weak"
    if len(text) > 1000 and any(candidate.evidence for candidate in candidates):
        return "good"
    return "partial"


def missing_work(*, status: str, families: list[EdgeFamily]) -> list[str]:
    work: list[str] = []
    if status in {"placeholder", "raw_url_only", "needs_extraction"}:
        work.append("extract full thread text before trusting this source")
    if not families:
        work.append("classify edge family after extraction")
    else:
        work.append("map every claim to required data and a falsifiable backtest")
    work.append("ignore posted PnL claims until reproduced in local paper/shadow runs")
    return work


def summarize_edge_map(analyses: list[ThreadEdgeAnalysis]) -> list[dict[str, object]]:
    by_family: dict[EdgeFamily, dict[str, object]] = {}
    for analysis in analyses:
        for family in analysis.edge_families:
            row = by_family.setdefault(
                family,
                {
                    "edge_family": family.value,
                    "threads": 0,
                    "candidates": 0,
                    "good_or_partial_evidence": 0,
                    "first_test": first_test_for(family),
                    "main_risk": main_risk_for(family),
                },
            )
            row["threads"] = int(row["threads"]) + 1
            row["candidates"] = int(row["candidates"]) + len(
                [candidate for candidate in analysis.candidates if candidate.edge_family == family]
            )
            if analysis.evidence_quality in {"good", "partial"}:
                row["good_or_partial_evidence"] = int(row["good_or_partial_evidence"]) + 1
    return sorted(by_family.values(), key=lambda row: (-int(row["candidates"]), str(row["edge_family"])))


def render_edge_synthesis_report(analyses: list[ThreadEdgeAnalysis]) -> str:
    status_counts = Counter(analysis.extraction_status for analysis in analyses)
    family_rows = summarize_edge_map(analyses)
    candidate_count = sum(len(analysis.candidates) for analysis in analyses)
    return f"""---
type: "edge-research-synthesis"
created: "{datetime.now(UTC).isoformat()}"
tags: ["research", "twitter", "edge-map"]
---
# Twitter Edge Synthesis

## Executive Read
- Threads scanned: {len(analyses)}
- Strategy candidates found: {candidate_count}
- Content-rich or partially extracted threads: {sum(count for status, count in status_counts.items() if status not in {"placeholder", "raw_url_only"})}
- Placeholder/raw URL threads: {status_counts.get("placeholder", 0) + status_counts.get("raw_url_only", 0)}

The current strongest direction is not a single viral strategy. It is a research pipeline: extract full thread text, classify the claim into a measurable edge family, backtest with realistic fill assumptions, then graduate only the survivors to paper/shadow runs.

## Edge Family Map
{_edge_family_table(family_rows)}

## Thread Triage
{_thread_triage_table(analyses)}

## Candidate Drilldown
{_candidate_drilldown(analyses)}

## Operating Rules
- Treat every Twitter PnL claim as a lead, not evidence.
- Promote only claims that can be expressed as orderbook/trade/latency features.
- Prefer edges that survive fees, slippage, queue priority, and inventory constraints.
- Keep Codex and LLMs off the order path; use them for research, review, reports, and tooling.
"""


def first_test_for(family: EdgeFamily) -> str:
    tests = {
        EdgeFamily.SPREAD_CAPTURE: "Replay wide-spread windows and require realistic passive fill assumptions.",
        EdgeFamily.MARKET_MAKING: "Paper quote both sides with inventory skew and adverse-selection tracking.",
        EdgeFamily.ORDERBOOK_IMBALANCE: "Measure forward mid-price move after imbalance spikes.",
        EdgeFamily.LIQUIDITY_VACUUM: "Scan thin books after price jumps and test conservative fade exits.",
        EdgeFamily.STALE_ORDERBOOK: "Compare snapshot age against trades and related market movement.",
        EdgeFamily.DELAYED_REPRICING: "Build paired-market lead/lag replay before any execution logic.",
        EdgeFamily.CROSS_MARKET_ARBITRAGE: "Monitor net executable gap across both legs with partial-fill penalties.",
        EdgeFamily.NEWS_LATENCY: "Replay timestamped news windows with strict source quality labels.",
        EdgeFamily.EVENT_DRIVEN_REPRICING: "Segment markets around scheduled event phases and compare spreads/fills.",
        EdgeFamily.BEHAVIORAL_OVERREACTION: "Manually label jumps, then test reversion only after spread stabilization.",
        EdgeFamily.RESOLUTION_EDGE: "Create rule checklist and manually label true outcome state near settlement.",
    }
    return tests[family]


def main_risk_for(family: EdgeFamily) -> str:
    risks = {
        EdgeFamily.SPREAD_CAPTURE: "Apparent fills disappear once queue priority and stale books are modeled.",
        EdgeFamily.MARKET_MAKING: "Inventory accumulates into adverse selection.",
        EdgeFamily.ORDERBOOK_IMBALANCE: "Displayed depth cancels before execution.",
        EdgeFamily.LIQUIDITY_VACUUM: "Thin books keep moving and exits are expensive.",
        EdgeFamily.STALE_ORDERBOOK: "Stale display may not be executable.",
        EdgeFamily.DELAYED_REPRICING: "Related-market mapping creates false positives.",
        EdgeFamily.CROSS_MARKET_ARBITRAGE: "One leg fills while the hedge leg fails.",
        EdgeFamily.NEWS_LATENCY: "Bad timestamps or low-quality news create fake edge.",
        EdgeFamily.EVENT_DRIVEN_REPRICING: "Event timing and market rules are ambiguous.",
        EdgeFamily.BEHAVIORAL_OVERREACTION: "The move is real information, not overreaction.",
        EdgeFamily.RESOLUTION_EDGE: "Rule interpretation errors dominate expected value.",
    }
    return risks[family]


def _clean_research_text(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        lowered = line.strip(" -").lower()
        if any(marker in lowered for marker in BOILERPLATE_MARKERS):
            continue
        lines.append(line)
    return "\n".join(line.strip() for line in lines if line.strip())


def _edge_family_table(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "No edge family has enough extracted evidence yet."
    lines = ["| Edge family | Threads | Candidates | First test | Main risk |", "|---|---:|---:|---|---|"]
    for row in rows:
        lines.append(
            f"| `{row['edge_family']}` | {row['threads']} | {row['candidates']} | "
            f"{row['first_test']} | {row['main_risk']} |"
        )
    return "\n".join(lines)


def _thread_triage_table(analyses: list[ThreadEdgeAnalysis]) -> str:
    lines = [
        "| Source | Status | Evidence | Families | Missing work |",
        "|---|---|---|---|---|",
    ]
    for analysis in analyses:
        families = ", ".join(f"`{family.value}`" for family in analysis.edge_families) or "none"
        missing = "; ".join(analysis.missing_work)
        source = analysis.source_url or analysis.source_path
        lines.append(
            f"| {source} | `{analysis.extraction_status}` | `{analysis.evidence_quality}` | {families} | {missing} |"
        )
    return "\n".join(lines)


def _candidate_drilldown(analyses: list[ThreadEdgeAnalysis]) -> str:
    candidates_by_family: dict[EdgeFamily, list[StrategyCandidate]] = defaultdict(list)
    for analysis in analyses:
        for candidate in analysis.candidates:
            candidates_by_family[candidate.edge_family].append(candidate)
    if not candidates_by_family:
        return "No candidate has enough extracted source text yet. Run the thread extraction workflow first."
    chunks: list[str] = []
    for family in sorted(candidates_by_family, key=lambda item: item.value):
        chunks.append(f"### {family.value}")
        for candidate in candidates_by_family[family]:
            evidence = candidate.evidence[0] if candidate.evidence else "No direct evidence sentence extracted."
            chunks.append(
                f"- **{candidate.name}** priority=`{candidate.priority}` difficulty=`{candidate.implementation_difficulty}`\n"
                f"  - Hypothesis: {candidate.hypothesis}\n"
                f"  - Evidence: {evidence}\n"
                f"  - Next: {candidate.next_action}"
            )
    return "\n".join(chunks)
