#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from polybot.knowledge.obsidian import ObsidianVault
from polybot.research.obsidian_mining import (
    ObsidianVaultReader,
    StrategyExtractor,
    parse_polymarket_threads,
)
from polybot.research.obsidian_mining.reporting import (
    render_strategy_candidate,
    render_strategy_candidate_index,
)
from polybot.research.strategy_registry import StrategyCandidateRegistry


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mine Obsidian Twitter thread notes for testable strategy candidates."
    )
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("obsidian-vault/Research/Strategy-Candidates/strategy-candidate-registry.json"),
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    reader = ObsidianVaultReader(args.vault)
    notes = reader.iter_markdown_notes()
    threads = parse_polymarket_threads(notes)
    candidates = StrategyExtractor().extract_from_threads(threads)

    if args.dry_run:
        print(f"Notes scanned: {len(notes)}")
        print(f"Twitter threads matched: {len(threads)}")
        print(f"Strategy candidates extracted: {len(candidates)}")
        for candidate in candidates:
            print(f"- {candidate.name} [{candidate.edge_family.value}] priority={candidate.priority}")
        return 0

    vault = ObsidianVault(args.vault)
    vault.ensure_structure()
    registry = StrategyCandidateRegistry(args.registry)
    registry.upsert_many(candidates)

    for candidate in candidates:
        vault.write_note(
            "Research/Strategy-Candidates",
            candidate.note_title,
            render_strategy_candidate(candidate),
            overwrite=args.overwrite,
        )
    vault.write_note(
        "Research/Strategy-Candidates",
        "Strategy Candidate Registry Index",
        render_strategy_candidate_index(candidates),
        overwrite=True,
    )

    print(f"Scanned {len(notes)} notes, matched {len(threads)} threads, wrote {len(candidates)} candidates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
