#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from polybot.agents.importer import clone_agent_repos
from polybot.knowledge.obsidian import ObsidianVault
from polybot.resources.markdown import render_agent_note
from polybot.resources.parsers import parse_agent_repos


def main() -> int:
    parser = argparse.ArgumentParser(description="Import external agent repositories and create notes.")
    parser.add_argument("--source", type=Path, default=Path("resources/agents-list"))
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    parser.add_argument("--target", type=Path, default=Path("external-agents"))
    parser.add_argument("--clone", dest="clone", action="store_true")
    parser.add_argument("--no-clone", dest="clone", action="store_false")
    parser.add_argument("--update-existing", action="store_true")
    parser.add_argument("--overwrite-notes", action="store_true")
    parser.set_defaults(clone=False)
    args = parser.parse_args()

    source = _resolve_source(args.source)
    repos = parse_agent_repos(source)

    if args.clone:
        for result in clone_agent_repos(
            repos=repos,
            target_dir=args.target,
            dry_run=False,
            update_existing=args.update_existing,
        ):
            print(f"{result.status}: {result.repo.url} -> {result.path}")

    vault = ObsidianVault(args.vault)
    vault.ensure_structure()
    written: list[Path] = []
    for repo in repos:
        path = vault.write_note(
            folder="Tools/Agents",
            title=repo.name,
            body=render_agent_note(repo),
            overwrite=args.overwrite_notes,
        )
        written.append(path)

    print(f"Imported {len(written)} agent notes. Cloning enabled: {args.clone}.")
    return 0


def _resolve_source(preferred: Path) -> Path:
    if preferred.exists():
        return preferred
    legacy = Path("Ressources/ressources_to_download.txt")
    if legacy.exists():
        return legacy
    return preferred


if __name__ == "__main__":
    raise SystemExit(main())

