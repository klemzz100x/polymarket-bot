from polybot.research.obsidian_mining.strategy_candidate import StrategyCandidate
from polybot.resources.markdown import render_frontmatter


def render_strategy_candidate(candidate: StrategyCandidate) -> str:
    metadata = {
        "type": "strategy-candidate",
        "candidate_id": candidate.candidate_id,
        "edge_family": candidate.edge_family.value,
        "priority": candidate.priority,
        "implementation_difficulty": candidate.implementation_difficulty,
        "source": candidate.source_obsidian_path,
        "source_url": candidate.source_url or "",
        "status": "new",
        "tags": ["strategy-candidate", "research", candidate.edge_family.value],
    }
    return f"""{render_frontmatter(metadata)}
# Strategy Candidate - {candidate.name}

## Source
- Obsidian: [[{candidate.source_obsidian_path.removesuffix(".md")}]]
- URL: {candidate.source_url or "n/a"}

## Summary
{candidate.summary}

## Hypothesis
{candidate.hypothesis}

## Edge Family
`{candidate.edge_family.value}`

## Required Data
{_bullets(candidate.required_data)}

## Metrics To Measure
{_bullets(candidate.metrics_to_measure)}

## Testable Signal
{candidate.testable_signal}

## Backtest Design
{candidate.backtest_design}

## Evidence
{_bullets(candidate.evidence or ["No direct evidence sentence extracted. Review source note manually."])}

## Risks
{candidate.main_risk}

## Implementation Difficulty
`{candidate.implementation_difficulty}`

## Priority
`{candidate.priority}`

## Next Actions
- {candidate.next_action}
- Link future backtest and paper-trading reports in the strategy registry.

## Links
- [[Research Loop]]
- [[Backtesting]]
- [[Paper Trading]]
- [[Data Layer]]
- [[Risk Management]]
"""


def render_strategy_candidate_index(candidates: list[StrategyCandidate]) -> str:
    lines = [
        f"- [[Research/Strategy-Candidates/{candidate.note_title}]] "
        f"`{candidate.edge_family.value}` priority=`{candidate.priority}`"
        for candidate in candidates
    ] or ["- No strategy candidates extracted yet."]
    return f"""{render_frontmatter({"type": "strategy-candidate-index", "tags": ["strategy-candidate", "research"]})}
# Strategy Candidate Registry Index

## Candidates
{chr(10).join(lines)}

## Review Rules
- Promote only candidates with clean data, measurable signals, and realistic paper/backtest behavior.
- Reject candidates that depend on unverifiable claims or impossible fills.
- Keep live trading out of scope.
"""


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)
