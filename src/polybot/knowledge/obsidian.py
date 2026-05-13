from pathlib import Path

from polybot.core.paths import PROJECT_DIRECTORIES
from polybot.resources.cleaners import slugify


class ObsidianVault:
    def __init__(self, root: Path) -> None:
        self.root = root

    def ensure_structure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for directory in PROJECT_DIRECTORIES:
            if directory.startswith("obsidian-vault/"):
                relative = directory.removeprefix("obsidian-vault/")
                (self.root / relative).mkdir(parents=True, exist_ok=True)

    def write_note(self, folder: str, title: str, body: str, overwrite: bool = False) -> Path:
        folder_path = self._safe_child(folder)
        folder_path.mkdir(parents=True, exist_ok=True)
        file_path = folder_path / f"{slugify(title)}.md"

        if file_path.exists() and not overwrite:
            return file_path

        file_path.write_text(body.rstrip() + "\n", encoding="utf-8")
        return file_path

    def _safe_child(self, relative: str) -> Path:
        root = self.root.resolve()
        candidate = (root / relative).resolve()
        if root != candidate and root not in candidate.parents:
            raise ValueError(f"Path escapes Obsidian vault: {relative}")
        return candidate

