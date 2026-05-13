from polybot.domain.models import AgentRepo, TwitterThreadSource
from polybot.resources.markdown import render_agent_note, render_twitter_thread_note


def test_render_thread_note_contains_required_sections() -> None:
    note = render_twitter_thread_note(
        TwitterThreadSource(
            url="https://x.com/example/status/123",
            author="example",
            status_id="123",
        )
    )

    assert "## Source" in note
    assert "## Idees exploitables" in note
    assert "[[Execution]]" in note


def test_render_agent_note_contains_repo() -> None:
    note = render_agent_note(
        AgentRepo(url="https://github.com/owner/repo", owner="owner", name="repo")
    )

    assert "## Repo" in note
    assert "https://github.com/owner/repo" in note
    assert "A tester" in note

