#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from polybot.knowledge.obsidian import ObsidianVault
from polybot.resources.markdown import render_twitter_thread_note
from polybot.resources.parsers import parse_twitter_thread_sources


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Twitter/X thread links into Obsidian notes.")
    parser.add_argument("--source", type=Path, default=Path("resources/twitter-threads"))
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = _resolve_source(args.source)
    threads = parse_twitter_thread_sources(source)
    vault = ObsidianVault(args.vault)

    if not args.dry_run:
        vault.ensure_structure()

    written: list[Path] = []
    for thread in threads:
        note = render_twitter_thread_note(thread)
        if args.dry_run:
            print(f"[dry-run] {thread.note_title} <- {thread.url}")
            continue
        path = vault.write_note(
            folder="Sources/Twitter-Threads",
            title=thread.note_title,
            body=note,
            overwrite=args.overwrite,
        )
        written.append(path)

    print(f"Imported {len(written) if not args.dry_run else len(threads)} Twitter thread notes.")
    return 0


def _resolve_source(preferred: Path) -> Path:
    if preferred.exists():
        return preferred
    legacy = Path("Ressources/Threads_twitter")
    if legacy.exists():
        return legacy
    return preferred


if __name__ == "__main__":
    raise SystemExit(main())

