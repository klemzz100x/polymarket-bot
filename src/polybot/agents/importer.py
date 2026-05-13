import subprocess
from pathlib import Path

from polybot.domain.models import AgentRepo, CloneResult


def clone_agent_repos(
    repos: list[AgentRepo],
    target_dir: Path,
    dry_run: bool = True,
    update_existing: bool = False,
) -> list[CloneResult]:
    target_dir.mkdir(parents=True, exist_ok=True)
    results: list[CloneResult] = []

    for repo in repos:
        destination = target_dir / repo.local_dir_name
        if dry_run:
            results.append(CloneResult(repo=repo, path=str(destination), status="dry_run"))
            continue

        if destination.exists():
            if update_existing:
                command = ["git", "-C", str(destination), "pull", "--ff-only"]
                status_label = "updated"
            else:
                results.append(CloneResult(repo=repo, path=str(destination), status="exists"))
                continue
        else:
            command = ["git", "clone", "--depth", "1", repo.url, str(destination)]
            status_label = "cloned"

        completed = subprocess.run(command, check=False, text=True, capture_output=True)
        if completed.returncode == 0:
            results.append(CloneResult(repo=repo, path=str(destination), status=status_label))
        else:
            results.append(
                CloneResult(
                    repo=repo,
                    path=str(destination),
                    status="failed",
                    message=(completed.stderr or completed.stdout).strip(),
                )
            )

    return results

