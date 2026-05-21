#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlparse

from polybot.knowledge.obsidian import ObsidianVault
from polybot.resources.cleaners import slugify
from polybot.resources.markdown import render_frontmatter


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote scraped Twitter/X excerpts into Obsidian source notes.")
    parser.add_argument("--source", type=Path, default=Path("resources/twitter-threads/scraped"))
    parser.add_argument("--vault", type=Path, default=Path("obsidian-vault"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    vault = ObsidianVault(args.vault)
    vault.ensure_structure()
    written: list[Path] = []
    for path in sorted(args.source.glob("*.md")):
        scraped = parse_scraped_note(path)
        if not scraped["source"] or len(scraped["body"]) < 40:
            continue
        title = f"Twitter Thread - {scraped['author']} - {scraped['status_id']}"
        note_path = vault.write_note(
            "Sources/Twitter-Threads",
            title,
            render_note(scraped),
            overwrite=args.overwrite,
        )
        written.append(note_path)

    print(f"Imported {len(written)} scraped Twitter excerpts into Obsidian.")
    for path in written[:10]:
        print(f"- {path}")
    return 0


def parse_scraped_note(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = [line.rstrip() for line in text.splitlines()]
    title = lines[0].removeprefix("# ").strip() if lines and lines[0].startswith("# ") else path.stem
    source = ""
    body_lines: list[str] = []
    for line in lines[1:]:
        if line.startswith("Source:"):
            source = line.removeprefix("Source:").strip()
            continue
        if line.strip():
            body_lines.append(line.strip())
    author, status_id = parse_twitter_identity(source)
    return {
        "title": title,
        "source": source,
        "author": author,
        "status_id": status_id,
        "body": "\n".join(body_lines).strip(),
    }


def parse_twitter_identity(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    author = parts[0] if parts else "unknown"
    status_id = "unknown"
    if len(parts) >= 3 and parts[1] in {"status", "statuses"}:
        status_id = parts[2]
    return author, status_id


def render_note(scraped: dict[str, str]) -> str:
    metadata = {
        "type": "twitter-thread",
        "source": scraped["source"],
        "author": scraped["author"],
        "status_id": scraped["status_id"],
        "status": "scraped_excerpt",
        "tags": ["source/twitter", "polymarket", "research", "scraped-excerpt"],
    }
    slug = slugify(f"{scraped['author']}-{scraped['status_id']}")
    return f"""{render_frontmatter(metadata)}
# Twitter Thread - {scraped["author"]} - {scraped["status_id"]}

## Source
{scraped["source"]}

## Resume
{scraped["body"]}

## Concepts cles
- A qualifier depuis l'extrait public.

## Idees exploitables
- Transformer l'extrait en hypothese testable seulement si le signal est mesurable.

## Strategies mentionnees
- A confirmer avec le thread complet si l'extrait est tronque.

## Risques / limites
- Extrait public incomplet.
- Claims de performance non audites.
- Le contenu complet du thread peut modifier l'interpretation.

## A tester
- Extraire le thread complet via export/source autorisee.
- Relier cette note a un backtest reproductible si une hypothese survit.

## Research Id
`{slug}`
"""


if __name__ == "__main__":
    raise SystemExit(main())
