from pathlib import Path

from polybot.resources.parsers import parse_agent_repos, parse_twitter_thread_sources


def test_parse_twitter_threads(tmp_path: Path) -> None:
    source = tmp_path / "threads.txt"
    source.write_text("https://x.com/example/status/123?s=20\n", encoding="utf-8")

    threads = parse_twitter_thread_sources(source)

    assert len(threads) == 1
    assert threads[0].author == "example"
    assert threads[0].status_id == "123"


def test_parse_agent_repos(tmp_path: Path) -> None:
    source = tmp_path / "agents.txt"
    source.write_text("https://github.com/owner/repo\n", encoding="utf-8")

    repos = parse_agent_repos(source)

    assert len(repos) == 1
    assert repos[0].owner == "owner"
    assert repos[0].name == "repo"

