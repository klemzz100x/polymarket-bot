import re

from polybot.research.obsidian_mining.hypothesis_generator import template_for
from polybot.research.obsidian_mining.strategy_candidate import EdgeFamily, StrategyCandidate
from polybot.research.obsidian_mining.thread_parser import TwitterThreadNote

EDGE_KEYWORDS: dict[EdgeFamily, tuple[str, ...]] = {
    EdgeFamily.SPREAD_CAPTURE: ("spread", "wide spread", "bid ask", "capture"),
    EdgeFamily.MARKET_MAKING: ("market making", "quote", "maker", "inventory", "two-sided"),
    EdgeFamily.ORDERBOOK_IMBALANCE: ("imbalance", "bid-heavy", "ask-heavy", "pressure"),
    EdgeFamily.LIQUIDITY_VACUUM: ("liquidity vacuum", "thin book", "low liquidity", "depth"),
    EdgeFamily.STALE_ORDERBOOK: ("stale", "old book", "cache", "slow update"),
    EdgeFamily.DELAYED_REPRICING: ("delayed repricing", "repricing delay", "lag", "lead-lag"),
    EdgeFamily.CROSS_MARKET_ARBITRAGE: ("arbitrage", "kalshi", "cross-market", "cross venue", "arb"),
    EdgeFamily.NEWS_LATENCY: ("news", "headline", "latency", "breaking"),
    EdgeFamily.EVENT_DRIVEN_REPRICING: ("event-driven", "event", "scheduled", "kickoff", "window"),
    EdgeFamily.BEHAVIORAL_OVERREACTION: ("overreaction", "panic", "retail", "behavioral", "fade"),
    EdgeFamily.RESOLUTION_EDGE: ("resolution", "settlement", "rules", "source of truth"),
}

PLACEHOLDER_MARKERS = (
    "a completer apres extraction",
    "a extraire",
    "source non auditee",
    "recherche a qualifier",
)

BOILERPLATE_MARKERS = (
    "verifier si le thread contient une hypothese testable",
    "transformer toute strategie mentionnee en spec de backtest",
    "classer les idees entre execution, pricing, market making, arbitrage, data ou tooling",
    "extraire le contenu via workflow n8n",
    "faire une note strategie separee",
    "lier les hypotheses a un backtest reproductible",
)


class StrategyExtractor:
    def extract_from_threads(self, threads: list[TwitterThreadNote]) -> list[StrategyCandidate]:
        candidates: list[StrategyCandidate] = []
        for thread in threads:
            candidates.extend(self.extract_from_thread(thread))
        return _dedupe_candidates(candidates)

    def extract_from_thread(self, thread: TwitterThreadNote) -> list[StrategyCandidate]:
        text = _remove_boilerplate(_normalize_text(thread.text))
        if _is_placeholder_only(text):
            return []
        families = detect_edge_families(text)
        candidates: list[StrategyCandidate] = []
        for family in families:
            template = template_for(family)
            evidence = _evidence_sentences(text, EDGE_KEYWORDS[family])
            name = _candidate_name(family, thread)
            candidates.append(
                StrategyCandidate(
                    name=name,
                    source_obsidian_path=thread.note.relative_path,
                    source_title=thread.note.title,
                    source_url=thread.source_url,
                    summary=_summary(evidence, fallback=thread.note.title),
                    hypothesis=template.hypothesis,
                    edge_family=family,
                    required_data=template.required_data,
                    metrics_to_measure=template.metrics_to_measure,
                    testable_signal=template.testable_signal,
                    backtest_design=template.backtest_design,
                    main_risk=template.main_risk,
                    implementation_difficulty=template.implementation_difficulty,
                    priority=_priority(template.priority, text=text, evidence=evidence),
                    next_action=template.next_action,
                    evidence=evidence[:5],
                )
            )
        return candidates


def detect_edge_families(text: str) -> list[EdgeFamily]:
    lowered = text.lower()
    scored: list[tuple[int, EdgeFamily]] = []
    for family, keywords in EDGE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > 0:
            scored.append((score, family))
    return [family for _score, family in sorted(scored, key=lambda item: (-item[0], item[1].value))]


def _is_placeholder_only(text: str) -> bool:
    lowered = text.lower()
    if len(lowered.strip()) < 120:
        return True
    marker_count = sum(1 for marker in PLACEHOLDER_MARKERS if marker in lowered)
    family_count = len(detect_edge_families(text))
    return marker_count >= 1 and family_count == 0


def _evidence_sentences(text: str, keywords: tuple[str, ...]) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+|\n+-\s+", text)
    evidence: list[str] = []
    for sentence in sentences:
        clean = " ".join(sentence.split()).strip(" -")
        if len(clean) < 20:
            continue
        lowered = clean.lower()
        if any(keyword in lowered for keyword in keywords):
            evidence.append(clean[:280])
    return evidence


def _summary(evidence: list[str], *, fallback: str) -> str:
    if evidence:
        return evidence[0]
    return f"Candidate extracted from {fallback}."


def _priority(base: str, *, text: str, evidence: list[str]) -> str:
    lowered = text.lower()
    if "backtest" in lowered or "test" in lowered:
        return base
    if not evidence and base == "high":
        return "medium"
    return base


def _candidate_name(family: EdgeFamily, thread: TwitterThreadNote) -> str:
    author = thread.author or thread.note.title.replace("Twitter Thread - ", "").split(" - ")[0]
    title = family.value.replace("_", " ").title()
    return f"{title} - {author}"


def _normalize_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _remove_boilerplate(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        lowered = line.lower().strip(" -.")
        if any(marker in lowered for marker in BOILERPLATE_MARKERS):
            continue
        lines.append(line)
    return "\n".join(lines)


def _dedupe_candidates(candidates: list[StrategyCandidate]) -> list[StrategyCandidate]:
    seen: set[str] = set()
    deduped: list[StrategyCandidate] = []
    for candidate in candidates:
        if candidate.candidate_id in seen:
            continue
        seen.add(candidate.candidate_id)
        deduped.append(candidate)
    return deduped
