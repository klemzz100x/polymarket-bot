#!/usr/bin/env python
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from polybot.knowledge.obsidian import ObsidianVault
from polybot.resources.cleaners import slugify
from polybot.resources.markdown import render_frontmatter


SOURCE_RE = re.compile(r"(?m)^Source\s*:\s*(?P<url>.+?)\s*$")
CONTENT_RE = re.compile(r"(?m)^(?:Content|Coentent)\s*:\s*(?P<title>.*)$")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")


@dataclass(frozen=True, slots=True)
class EdgeTemplate:
    label: str
    keywords: tuple[str, ...]
    thesis: str
    data_required: tuple[str, ...]
    first_test: str
    risk: str
    priority: str
    value_type: str
    min_score: int = 1


@dataclass(frozen=True, slots=True)
class ThreadAnalysis:
    source: str
    author: str
    status_id: str
    title: str
    slug: str
    text_chars: int
    primary_family: str
    families: list[str]
    relevance: str
    priority: str
    evidence: list[str]
    actionable_takeaways: list[str]
    hypotheses: list[dict[str, object]]
    caveats: list[str]


EDGE_TEMPLATES: tuple[EdgeTemplate, ...] = (
    EdgeTemplate(
        label="weather_event_discovery",
        keywords=("weather", "forecast", "rain", "temperature", "hurricane", "openweathermap", "noaa", "meteo"),
        thesis="Weather markets can be found and repriced faster by mapping forecast updates to active Polymarket markets.",
        data_required=("market metadata", "weather API snapshots", "forecast timestamps", "orderbooks", "trades"),
        first_test="For each weather thread claim, replay forecast update times against market mid-price changes and spread.",
        risk="Forecast source mismatch or ambiguous market wording can create false positives.",
        priority="high",
        value_type="market_selection",
    ),
    EdgeTemplate(
        label="news_latency",
        keywords=("news to price", "headline", "300 ms", "before you finish reading", "rss", "breaking news", "feed latency"),
        thesis="News-to-price latency can create short windows where Polymarket reprices slower than credible external feeds.",
        data_required=("news timestamps", "feed latency", "orderbooks", "trades", "market mapping"),
        first_test="Replay timestamped news events and measure time-to-midpoint-move with simulated execution latency.",
        risk="Bad source quality, timestamp drift, or already-priced information can erase the edge.",
        priority="high",
        value_type="latency_signal",
    ),
    EdgeTemplate(
        label="crypto_5m_microstructure",
        keywords=("5-minute", "5 minute", "btc up/down", "binance", "minute 1", "up/down trading", "crypto market"),
        thesis="Very short crypto markets may have repeatable early-window patterns if CEX microstructure leads Polymarket.",
        data_required=("Binance second data", "Polymarket 5m orderbooks", "trades", "market start/end times"),
        first_test="Rebuild 5m windows and test minute-1 direction, reversal, momentum, spread, and fill assumptions.",
        risk="Backtest leakage, survivorship bias, and queue priority can make a paper edge non-executable.",
        priority="high",
        value_type="pricing_signal",
    ),
    EdgeTemplate(
        label="information_theory_pricing",
        keywords=("information theory", "kelly", "bits", "entropy", "log odds", "bayes", "base rate"),
        thesis="Pricing decisions should be expressed as probability deltas and information gain, not narrative conviction.",
        data_required=("base rates", "market price history", "event labels", "fees", "position sizing"),
        first_test="Build a fair-value notebook that converts evidence updates into probability and expected log-growth.",
        risk="Subjective probability updates can hide overfitting if not tied to measurable event data.",
        priority="medium",
        value_type="pricing_framework",
    ),
    EdgeTemplate(
        label="markov_regime_model",
        keywords=("markov", "transition matrix", "regime model", "hidden markov", "walk-forward", "state transition"),
        thesis="Regime models can gate strategies so the bot trades only when market state supports the edge.",
        data_required=("returns", "spreads", "depth", "volatility", "state labels", "walk-forward splits"),
        first_test="Estimate regimes from historical windows and compare strategy performance by state out of sample.",
        risk="Transition probabilities are non-stationary and can overfit small samples.",
        priority="medium",
        value_type="model_filter",
    ),
    EdgeTemplate(
        label="neural_signal_model",
        keywords=("neural network", "lstm", "transformer", "feature vector", "model training", "gradient descent"),
        thesis="Neural models are useful only if they consume clean microstructure features and beat simple baselines.",
        data_required=("features", "labels", "walk-forward splits", "baseline models", "execution simulation"),
        first_test="Train a tiny baseline model first, then require neural models to beat it after costs and latency.",
        risk="Deep models can memorize noisy patterns and produce non-executable signals.",
        priority="low",
        value_type="model_filter",
    ),
    EdgeTemplate(
        label="smart_money_wallet_tracking",
        keywords=("wallet", "smart money", "address", "copy trading", "profiting wallet", "onchain"),
        thesis="Wallet tracking may identify repeatable market selection patterns, but direct copy trading is dangerous.",
        data_required=("wallet trades", "market metadata", "entry timestamps", "exit timestamps", "PnL attribution"),
        first_test="Rank wallets by out-of-sample hit rate, market category, entry timing, and drawdown, not headline PnL.",
        risk="Copying delayed fills creates adverse selection; public wallet lists decay quickly.",
        priority="medium",
        value_type="research_signal",
    ),
    EdgeTemplate(
        label="behavioral_bias_fade",
        keywords=("bias", "cognitive bias", "overreaction", "panic", "herd", "retail", "mispricing"),
        thesis="Behavioral narratives can become fade candidates when price jumps are unsupported by durable depth.",
        data_required=("price jumps", "volume spikes", "orderbook imbalance", "news labels", "reversion windows"),
        first_test="Label jump events and test reversion only after spread stabilizes and depth returns.",
        risk="What looks like bias may be correct information arrival.",
        priority="medium",
        value_type="pricing_signal",
    ),
    EdgeTemplate(
        label="strategy_validation_pipeline",
        keywords=("strategy_validator", "validator", "validation checklist", "backtest", "paper trading", "shadow trading", "validate strategy"),
        thesis="A strict validation checklist is an edge because it kills weak ideas before they reach paper/live systems.",
        data_required=("strategy specs", "backtest reports", "paper runs", "shadow runs", "failure reasons"),
        first_test="Require every candidate to pass data availability, execution realism, risk, and falsifiability checks.",
        risk="Checklist theater can replace real tests if it is not tied to metrics.",
        priority="high",
        value_type="research_infra",
    ),
    EdgeTemplate(
        label="agentic_research_infra",
        keywords=("obsidian", "vault", "mcp", "n8n", "claude", "agent", "generated output"),
        thesis="Agentic research infrastructure compounds iteration speed by turning raw sources into structured hypotheses.",
        data_required=("source notes", "candidate registry", "run reports", "dashboards", "automation logs"),
        first_test="Measure time from raw thread to testable strategy spec and reduce manual steps with safe automations.",
        risk="Automation can amplify low-quality sources if extraction quality is not tracked.",
        priority="high",
        value_type="research_infra",
    ),
    EdgeTemplate(
        label="simplification_robustness",
        keywords=("deleted half", "half my bot", "simple bot", "complexity", "less code", "mistakes"),
        thesis="Simpler strategies and smaller execution surfaces may outperform complex bots by reducing failure modes.",
        data_required=("strategy variants", "code complexity metrics", "paper/shadow performance", "error logs"),
        first_test="Compare simple baseline strategies against complex variants with identical data and execution assumptions.",
        risk="Over-simplifying can remove real risk controls or necessary market filters.",
        priority="medium",
        value_type="engineering_edge",
    ),
    EdgeTemplate(
        label="bot_tooling_stack",
        keywords=("tools under the hood", "stack", "deployment", "python bot", "telegram alert", "dashboard", "monitoring"),
        thesis="Tooling threads can improve the bot's operating model even when they do not contain a trading signal.",
        data_required=("runbooks", "service health", "alerts", "operator actions", "incident logs"),
        first_test="Convert useful tooling claims into runbook/dashboard/alert requirements, not strategy candidates.",
        risk="Tool fascination can distract from measurable market edge.",
        priority="medium",
        value_type="ops_infra",
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import full raw Twitter threads and extract a usable edge backlog.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("resources/twitter-threads/full-content/Threads_twitter_content.txt"),
    )
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    parser.add_argument("--json-out", type=Path, default=Path("resources/twitter-threads/full-content/thread_value_matrix.json"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    threads = parse_raw_threads(args.source)
    analyses = [analyze_thread(thread) for thread in threads]

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps([asdict(analysis) for analysis in analyses], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    vault = ObsidianVault(args.vault)
    vault.ensure_structure()
    for thread, analysis in zip(threads, analyses, strict=True):
        vault.write_note(
            "Sources/Twitter-Threads",
            f"Full Thread - {analysis.author} - {analysis.status_id}",
            render_full_thread_note(thread, analysis),
            overwrite=args.overwrite,
        )
    matrix_path = vault.write_note(
        "Research/Edge-Research",
        "Thread Value Matrix",
        render_value_matrix(analyses),
        overwrite=True,
    )
    backlog_path = vault.write_note(
        "Research/Edge-Research",
        "Edge Backlog From Full Threads",
        render_edge_backlog(analyses),
        overwrite=True,
    )

    family_counts = Counter(family for analysis in analyses for family in analysis.families)
    print(f"Parsed {len(threads)} full threads.")
    print(f"JSON={args.json_out}")
    print(f"Matrix={matrix_path}")
    print(f"Backlog={backlog_path}")
    for family, count in family_counts.most_common():
        print(f"- {family}: {count}")
    return 0


def parse_raw_threads(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8-sig")
    starts = [match.start() for match in SOURCE_RE.finditer(text)]
    blocks = [text[start : starts[index + 1] if index + 1 < len(starts) else len(text)] for index, start in enumerate(starts)]
    threads: list[dict[str, str]] = []
    for block in blocks:
        source_match = SOURCE_RE.search(block)
        if not source_match:
            continue
        content_match = CONTENT_RE.search(block)
        source = source_match.group("url").strip()
        title = content_match.group("title").strip() if content_match else ""
        body = block[content_match.end() :] if content_match else block[source_match.end() :]
        body = "\n".join(line.rstrip() for line in body.strip().splitlines())
        author, status_id = parse_twitter_identity(source)
        threads.append(
            {
                "source": source,
                "author": author,
                "status_id": status_id,
                "title": title or first_nonempty_line(body) or "Untitled thread",
                "body": body,
            }
        )
    return threads


def analyze_thread(thread: dict[str, str]) -> ThreadAnalysis:
    body = clean_text(thread["body"])
    matches = matched_templates(body, thread["title"])
    families = [template.label for template, _score in matches]
    primary = families[0] if families else "unclassified"
    hypotheses = [hypothesis_from_template(template, body) for template, _score in matches[:4]]
    evidence = evidence_sentences(body, matches[:4])
    relevance = classify_relevance(matches)
    priority = choose_priority(matches, relevance)
    takeaways = actionable_takeaways(matches)
    caveats = caveats_for(thread, matches)
    return ThreadAnalysis(
        source=thread["source"],
        author=thread["author"],
        status_id=thread["status_id"],
        title=thread["title"],
        slug=slugify(f"{thread['author']}-{thread['status_id']}-{thread['title']}"),
        text_chars=len(body),
        primary_family=primary,
        families=families,
        relevance=relevance,
        priority=priority,
        evidence=evidence,
        actionable_takeaways=takeaways,
        hypotheses=hypotheses,
        caveats=caveats,
    )


def matched_templates(body: str, title: str) -> list[tuple[EdgeTemplate, int]]:
    lowered = f"{title}\n{body}".lower()
    scored: list[tuple[EdgeTemplate, int]] = []
    for template in EDGE_TEMPLATES:
        score = sum(1 for keyword in template.keywords if keyword in lowered)
        if score >= template.min_score:
            scored.append((template, score))
    return sorted(scored, key=lambda item: (-item[1], priority_score(item[0].priority), item[0].label))


def hypothesis_from_template(template: EdgeTemplate, body: str) -> dict[str, object]:
    return {
        "family": template.label,
        "value_type": template.value_type,
        "thesis": template.thesis,
        "required_data": list(template.data_required),
        "first_test": template.first_test,
        "risk": template.risk,
        "priority": template.priority,
        "evidence": evidence_for_template(body, template)[:3],
    }


def evidence_sentences(body: str, matches: list[tuple[EdgeTemplate, int]]) -> list[str]:
    evidence: list[str] = []
    for template, _score in matches:
        evidence.extend(evidence_for_template(body, template))
    deduped = list(dict.fromkeys(evidence))
    return deduped[:8]


def evidence_for_template(body: str, template: EdgeTemplate) -> list[str]:
    sentences: list[str] = []
    for sentence in SENTENCE_RE.split(body):
        clean = " ".join(sentence.split()).strip()
        if len(clean) < 35:
            continue
        lowered = clean.lower()
        if any(keyword in lowered for keyword in template.keywords):
            sentences.append(clean[:320])
    return sentences


def actionable_takeaways(matches: list[tuple[EdgeTemplate, int]]) -> list[str]:
    if not matches:
        return ["Keep as source material; no directly testable trading or infrastructure edge was detected yet."]
    return [template.first_test for template, _score in matches[:4]]


def caveats_for(thread: dict[str, str], matches: list[tuple[EdgeTemplate, int]]) -> list[str]:
    caveats = ["Do not treat posted PnL, win rate, or screenshots as evidence until reproduced locally."]
    if "t.me/" in thread["body"].lower() or "private group" in thread["body"].lower():
        caveats.append("Contains community/group promotion; separate useful mechanics from marketing.")
    if not matches:
        caveats.append("No matching edge family; review manually before promoting.")
    if len(thread["body"]) < 800:
        caveats.append("Short thread body; may need source review for missing context.")
    return caveats


def classify_relevance(matches: list[tuple[EdgeTemplate, int]]) -> str:
    if not matches:
        return "source_material"
    value_types = {template.value_type for template, _score in matches}
    if value_types & {"pricing_signal", "latency_signal", "market_selection"}:
        return "direct_edge"
    if value_types & {"research_signal", "model_filter"}:
        return "research_edge"
    return "infrastructure_edge"


def choose_priority(matches: list[tuple[EdgeTemplate, int]], relevance: str) -> str:
    if not matches:
        return "low"
    if relevance == "direct_edge" and any(template.priority == "high" for template, _score in matches):
        return "high"
    if any(template.priority == "high" for template, _score in matches):
        return "medium"
    return matches[0][0].priority


def render_full_thread_note(thread: dict[str, str], analysis: ThreadAnalysis) -> str:
    metadata = {
        "type": "twitter-thread",
        "source": thread["source"],
        "author": thread["author"],
        "status_id": thread["status_id"],
        "status": "full_content_imported",
        "primary_family": analysis.primary_family,
        "priority": analysis.priority,
        "relevance": analysis.relevance,
        "tags": ["source/twitter", "polymarket", "research", "full-content"],
    }
    return f"""{render_frontmatter(metadata)}
# Full Thread - {thread["author"]} - {thread["status_id"]}

## Source
{thread["source"]}

## Title
{thread["title"]}

## Extraction Summary
- Relevance: `{analysis.relevance}`
- Primary family: `{analysis.primary_family}`
- Priority: `{analysis.priority}`
- Families: {", ".join(f"`{family}`" for family in analysis.families) or "none"}

## Actionable Takeaways
{bullets(analysis.actionable_takeaways)}

## Hypotheses
{render_hypotheses(analysis.hypotheses)}

## Evidence
{bullets(analysis.evidence or ["No strong evidence sentence detected."])}

## Caveats
{bullets(analysis.caveats)}

## Raw Thread
```text
{thread["body"].strip()}
```
"""


def render_value_matrix(analyses: list[ThreadAnalysis]) -> str:
    lines = [
        "| Priority | Relevance | Primary family | Source | First actionable step |",
        "|---|---|---|---|---|",
    ]
    for analysis in sorted(analyses, key=lambda item: (priority_order(item.priority), item.primary_family, item.author)):
        step = analysis.actionable_takeaways[0] if analysis.actionable_takeaways else "Manual review."
        lines.append(
            f"| `{analysis.priority}` | `{analysis.relevance}` | `{analysis.primary_family}` | "
            f"[{analysis.author}]({analysis.source}) | {step} |"
        )
    family_counts = Counter(family for analysis in analyses for family in analysis.families)
    return f"""{render_frontmatter({"type": "thread-value-matrix", "tags": ["research", "twitter", "edge"]})}
# Thread Value Matrix

## Summary
- Full threads parsed: {len(analyses)}
- Direct edge threads: {sum(1 for item in analyses if item.relevance == "direct_edge")}
- Research edge threads: {sum(1 for item in analyses if item.relevance == "research_edge")}
- Infrastructure edge threads: {sum(1 for item in analyses if item.relevance == "infrastructure_edge")}

## Family Counts
{bullets([f"`{family}`: {count}" for family, count in family_counts.most_common()] or ["No families detected."])}

## Matrix
{chr(10).join(lines)}
"""


def render_edge_backlog(analyses: list[ThreadAnalysis]) -> str:
    grouped: dict[str, list[ThreadAnalysis]] = defaultdict(list)
    for analysis in analyses:
        grouped[analysis.primary_family].append(analysis)

    sections: list[str] = []
    for family in sorted(grouped):
        sections.append(f"## {family}")
        for analysis in sorted(grouped[family], key=lambda item: priority_order(item.priority)):
            sections.append(
                f"### [{analysis.title}]({analysis.source})\n"
                f"- Priority: `{analysis.priority}`\n"
                f"- Relevance: `{analysis.relevance}`\n"
                f"- First step: {analysis.actionable_takeaways[0] if analysis.actionable_takeaways else 'Manual review.'}\n"
                f"- Main caveat: {analysis.caveats[0] if analysis.caveats else 'n/a'}\n"
                f"- Evidence: {analysis.evidence[0] if analysis.evidence else 'No strong evidence sentence detected.'}\n"
            )
    return f"""{render_frontmatter({"type": "edge-backlog", "tags": ["research", "twitter", "edge-backlog"]})}
# Edge Backlog From Full Threads

This backlog converts raw Twitter/X thread text into testable research work. It is intentionally skeptical: claims become work items only after they map to data, execution assumptions, and a falsifiable test.

{chr(10).join(sections)}
"""


def render_hypotheses(hypotheses: list[dict[str, object]]) -> str:
    if not hypotheses:
        return "- No testable hypothesis detected."
    chunks: list[str] = []
    for item in hypotheses:
        chunks.append(
            f"### {item['family']}\n"
            f"- Thesis: {item['thesis']}\n"
            f"- Value type: `{item['value_type']}`\n"
            f"- Required data: {', '.join(f'`{value}`' for value in item['required_data'])}\n"
            f"- First test: {item['first_test']}\n"
            f"- Risk: {item['risk']}\n"
            f"- Priority: `{item['priority']}`"
        )
    return "\n\n".join(chunks)


def parse_twitter_identity(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    author = parts[0] if parts else "unknown"
    status_id = "unknown"
    if len(parts) >= 3 and parts[1] in {"status", "statuses"}:
        status_id = parts[2]
    return author, status_id


def first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        if clean:
            return clean
    return ""


def clean_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").splitlines()).strip()


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def priority_score(priority: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(priority, 0)


def priority_order(priority: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(priority, 3)


if __name__ == "__main__":
    raise SystemExit(main())
