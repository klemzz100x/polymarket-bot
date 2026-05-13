from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

from polybot.resources.cleaners import clean_resource_text, slugify
from polybot.resources.parsers import parse_twitter_thread_sources


@dataclass(frozen=True, slots=True)
class ScrapedThread:
    url: str
    title: str
    text: str
    raw_payload: dict[str, Any]


class TwitterThreadScraper:
    """Best-effort public scraper.

    This intentionally avoids authenticated scraping or anti-bot bypasses. It uses the public
    publish.twitter.com oEmbed endpoint when available and stores whatever public excerpt it can get.
    Full thread capture is better handled by a user-provided export or an approved data provider.
    """

    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def scrape_url(self, url: str) -> ScrapedThread:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                "https://publish.twitter.com/oembed",
                params={"url": url, "omit_script": "true", "dnt": "true"},
                headers={"User-Agent": "polybot-research-scraper/0.1"},
            )
            response.raise_for_status()
            payload = response.json()

        html = str(payload.get("html") or "")
        text = _html_to_text(html)
        title = str(payload.get("author_name") or "Twitter Thread")
        return ScrapedThread(url=url, title=title, text=text, raw_payload=payload)

    async def scrape_source_file(self, source: Path, output_dir: Path) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        for thread in parse_twitter_thread_sources(source):
            scraped = await self.scrape_url(thread.url)
            filename = slugify(thread.note_title) + ".md"
            path = output_dir / filename
            path.write_text(
                f"# {scraped.title}\n\nSource: {scraped.url}\n\n{scraped.text}\n",
                encoding="utf-8",
            )
            written.append(path)
        return written


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return clean_resource_text(soup.get_text("\n"))

