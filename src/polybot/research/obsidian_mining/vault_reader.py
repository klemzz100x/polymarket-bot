from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class MarkdownNote:
    path: Path
    vault_root: Path
    title: str
    frontmatter: dict[str, Any]
    body: str
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def relative_path(self) -> str:
        return self.path.relative_to(self.vault_root).as_posix()

    @property
    def obsidian_link(self) -> str:
        return f"[[{self.path.with_suffix('').relative_to(self.vault_root).as_posix()}]]"


class ObsidianVaultReader:
    def __init__(self, vault_root: Path) -> None:
        self.vault_root = vault_root

    def iter_markdown_notes(self) -> list[MarkdownNote]:
        if not self.vault_root.exists():
            return []
        notes: list[MarkdownNote] = []
        for path in sorted(self.vault_root.rglob("*.md")):
            if ".obsidian" in path.parts:
                continue
            notes.append(parse_markdown_note(path, self.vault_root))
        return notes


def parse_markdown_note(path: Path, vault_root: Path) -> MarkdownNote:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    title = _extract_title(body) or path.stem
    return MarkdownNote(
        path=path,
        vault_root=vault_root,
        title=title,
        frontmatter=frontmatter,
        body=body.strip(),
        sections=_extract_sections(body),
    )


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    body = text[end + 4 :].lstrip()
    return _parse_frontmatter(raw), body


def _parse_frontmatter(raw: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = _parse_scalar(value.strip())
    return data


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        items = value[1:-1].split(",")
        return [_unquote(item.strip()) for item in items if item.strip()]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return _unquote(value)


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1].replace('\\"', '"')
    return value


def _extract_title(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return None


def _extract_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        if line.startswith("## "):
            current = line.removeprefix("## ").strip()
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
    return {key: "\n".join(lines).strip() for key, lines in sections.items()}
