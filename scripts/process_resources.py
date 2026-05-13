#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from polybot.knowledge.obsidian import ObsidianVault
from polybot.resources.markdown import render_agent_note, render_twitter_thread_note
from polybot.resources.parsers import parse_agent_repos, parse_twitter_thread_sources


def main() -> int:
    parser = argparse.ArgumentParser(description="Process raw resources into clean Obsidian notes.")
    parser.add_argument("--resources", type=Path, default=Path("resources"))
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    vault = ObsidianVault(args.vault)
    vault.ensure_structure()

    count = 0
    for thread in parse_twitter_thread_sources(args.resources / "twitter-threads"):
        vault.write_note(
            "Sources/Twitter-Threads",
            thread.note_title,
            render_twitter_thread_note(thread),
            overwrite=args.overwrite,
        )
        count += 1

    for repo in parse_agent_repos(args.resources / "agents-list"):
        vault.write_note(
            "Tools/Agents",
            repo.name,
            render_agent_note(repo),
            overwrite=args.overwrite,
        )
        count += 1

    print(f"Processed {count} resources into Obsidian notes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

