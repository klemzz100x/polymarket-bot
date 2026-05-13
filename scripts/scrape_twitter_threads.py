#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from polybot.resources.scraping import TwitterThreadScraper


async def run() -> int:
    parser = argparse.ArgumentParser(description="Best-effort public scraping for Twitter/X thread links.")
    parser.add_argument("--source", type=Path, default=Path("resources/twitter-threads"))
    parser.add_argument("--output", type=Path, default=Path("resources/twitter-threads/scraped"))
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    scraper = TwitterThreadScraper(timeout_seconds=args.timeout)
    written = await scraper.scrape_source_file(args.source, args.output)
    print(f"Scraped {len(written)} public thread excerpts into {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))

