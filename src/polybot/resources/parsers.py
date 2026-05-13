import re
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlparse

from polybot.domain.models import AgentRepo, TwitterThreadSource
from polybot.resources.cleaners import clean_resource_text

URL_RE = re.compile(r"https?://[^\s<>\]\)\"']+")
TEXT_SUFFIXES = {".txt", ".md", ".csv", ".json", ""}


def extract_urls(text: str) -> list[str]:
    urls = [match.group(0).rstrip(".,;") for match in URL_RE.finditer(text)]
    return list(dict.fromkeys(urls))


def iter_text_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return

    if not path.exists():
        return

    for item in sorted(path.rglob("*")):
        if item.is_file() and item.suffix.lower() in TEXT_SUFFIXES:
            yield item


def read_text_corpus(path: Path) -> str:
    chunks: list[str] = []
    for file_path in iter_text_files(path):
        try:
            chunks.append(file_path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            chunks.append(file_path.read_text(encoding="latin-1"))
    return clean_resource_text("\n".join(chunks))


def parse_twitter_thread_sources(path: Path) -> list[TwitterThreadSource]:
    text = read_text_corpus(path)
    sources: list[TwitterThreadSource] = []

    for url in extract_urls(text):
        parsed = urlparse(url)
        host = parsed.netloc.lower().removeprefix("www.")
        if host not in {"x.com", "twitter.com", "mobile.twitter.com"}:
            continue

        parts = [part for part in parsed.path.split("/") if part]
        author: str | None = None
        status_id: str | None = None
        if len(parts) >= 3 and parts[1] == "status":
            author = parts[0]
            status_id = parts[2]

        sources.append(TwitterThreadSource(url=url, author=author, status_id=status_id))

    return _dedupe_threads(sources)


def parse_agent_repos(path: Path) -> list[AgentRepo]:
    text = read_text_corpus(path)
    repos: list[AgentRepo] = []

    for url in extract_urls(text):
        parsed = urlparse(url)
        host = parsed.netloc.lower().removeprefix("www.")
        if host != "github.com":
            continue

        parts = [part.removesuffix(".git") for part in parsed.path.split("/") if part]
        if len(parts) < 2:
            continue

        repos.append(AgentRepo(url=url, owner=parts[0], name=parts[1]))

    return _dedupe_repos(repos)


def _dedupe_threads(items: list[TwitterThreadSource]) -> list[TwitterThreadSource]:
    seen: set[str] = set()
    deduped: list[TwitterThreadSource] = []
    for item in items:
        key = item.status_id or item.url
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _dedupe_repos(items: list[AgentRepo]) -> list[AgentRepo]:
    seen: set[str] = set()
    deduped: list[AgentRepo] = []
    for item in items:
        key = f"{item.owner}/{item.name}".lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped

