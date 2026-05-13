from dataclasses import dataclass

from polybot.research.obsidian_mining.vault_reader import MarkdownNote


@dataclass(frozen=True, slots=True)
class TwitterThreadNote:
    note: MarkdownNote
    source_url: str | None
    author: str | None
    status_id: str | None
    text: str

    @property
    def source_link(self) -> str:
        return self.note.obsidian_link


def is_polymarket_twitter_thread(note: MarkdownNote) -> bool:
    note_type = str(note.frontmatter.get("type", ""))
    path = note.relative_path.lower()
    text = note.body.lower()
    is_thread = note_type == "twitter-thread" or "sources/twitter-threads" in path
    is_relevant = any(
        keyword in text
        for keyword in (
            "polymarket",
            "prediction market",
            "orderbook",
            "market making",
            "arbitrage",
            "execution",
            "inefficien",
        )
    )
    return is_thread and is_relevant


def parse_twitter_thread_note(note: MarkdownNote) -> TwitterThreadNote:
    source_url = str(note.frontmatter.get("source") or "").strip() or None
    author = str(note.frontmatter.get("author") or "").strip() or None
    status_id = str(note.frontmatter.get("status_id") or "").strip() or None
    sections = "\n\n".join(
        value
        for key, value in note.sections.items()
        if key.lower()
        in {
            "resume",
            "résumé",
            "concepts cles",
            "concepts clés",
            "idees exploitables",
            "idées exploitables",
            "strategies mentionnees",
            "stratégies mentionnées",
            "a tester",
            "à tester",
        }
    )
    text = sections or note.body
    return TwitterThreadNote(
        note=note,
        source_url=source_url,
        author=author,
        status_id=status_id,
        text=text,
    )


def parse_polymarket_threads(notes: list[MarkdownNote]) -> list[TwitterThreadNote]:
    return [parse_twitter_thread_note(note) for note in notes if is_polymarket_twitter_thread(note)]
