#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from polybot.knowledge.obsidian import ObsidianVault
from polybot.resources.markdown import render_generic_note


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a clean Markdown note in the Obsidian vault.")
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    parser.add_argument("--folder", default="Ideas")
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", default="")
    parser.add_argument("--body-file", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    body = args.body
    if args.body_file:
        body = args.body_file.read_text(encoding="utf-8")

    vault = ObsidianVault(args.vault)
    vault.ensure_structure()
    note = render_generic_note(title=args.title, body=body, metadata={"status": "draft"})
    path = vault.write_note(args.folder, args.title, note, overwrite=args.overwrite)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

