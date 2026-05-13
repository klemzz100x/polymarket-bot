from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MarkdownDocument:
    path: Path
    title: str
    body: str
    tags: list[str]


class MarkdownVaultLoader:
    def __init__(self, vault_dir: Path) -> None:
        self.vault_dir = vault_dir

    def load(self) -> list[MarkdownDocument]:
        documents: list[MarkdownDocument] = []
        for path in sorted(self.vault_dir.rglob("*.md")):
            body = path.read_text(encoding="utf-8")
            title = _extract_title(body) or path.stem
            documents.append(MarkdownDocument(path=path, title=title, body=body, tags=[]))
        return documents


def _extract_title(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return None

