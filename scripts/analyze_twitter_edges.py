#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from polybot.knowledge.obsidian import ObsidianVault
from polybot.research.obsidian_mining import ObsidianVaultReader
from polybot.research.obsidian_mining.edge_synthesis import (
    analyze_threads,
    render_edge_synthesis_report,
    summarize_edge_map,
)
from polybot.research.obsidian_mining.thread_parser import parse_twitter_thread_note


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze Twitter/X research notes into a thread-by-thread edge synthesis."
    )
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    parser.add_argument("--folder", default="Research/Edge-Research")
    parser.add_argument("--title", default="Twitter Edge Synthesis")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    notes = ObsidianVaultReader(args.vault).iter_markdown_notes()
    threads = [
        parse_twitter_thread_note(note)
        for note in notes
        if str(note.frontmatter.get("type", "")) == "twitter-thread"
        or "sources/twitter-threads" in note.relative_path.lower()
    ]
    analyses = analyze_threads(threads)
    edge_map = summarize_edge_map(analyses)

    print(f"Notes scanned: {len(notes)}")
    print(f"Twitter threads matched: {len(threads)}")
    print(f"Edge families detected: {len(edge_map)}")
    print(f"Strategy candidates detected: {sum(len(item.candidates) for item in analyses)}")
    for row in edge_map:
        print(
            f"- {row['edge_family']}: threads={row['threads']} "
            f"candidates={row['candidates']} first_test={row['first_test']}"
        )

    if args.dry_run:
        return 0

    vault = ObsidianVault(args.vault)
    vault.ensure_structure()
    path = vault.write_note(
        args.folder,
        args.title,
        render_edge_synthesis_report(analyses),
        overwrite=args.overwrite,
    )
    print(f"Obsidian={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
