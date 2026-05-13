from pathlib import Path


PROJECT_DIRECTORIES: tuple[str, ...] = (
    "resources/twitter-threads",
    "resources/agents-list",
    "external-agents",
    "obsidian-vault/Research",
    "obsidian-vault/Research/Strategy-Candidates",
    "obsidian-vault/Strategies",
    "obsidian-vault/Backtests",
    "obsidian-vault/Architecture",
    "obsidian-vault/Trading-Journal",
    "obsidian-vault/Post-Mortems",
    "obsidian-vault/Market-Research",
    "obsidian-vault/Data",
    "obsidian-vault/Paper-Trading",
    "obsidian-vault/Evaluation",
    "obsidian-vault/Performance",
    "obsidian-vault/Shadow-Trading",
    "obsidian-vault/Live-Readiness",
    "obsidian-vault/Live-Execution",
    "obsidian-vault/OMS",
    "obsidian-vault/Risk",
    "obsidian-vault/Research/Inefficiencies",
    "obsidian-vault/Execution",
    "obsidian-vault/Risk-Management",
    "obsidian-vault/Ideas",
    "obsidian-vault/Tools/Agents",
    "obsidian-vault/Tools/Skills",
    "obsidian-vault/Sources/Twitter-Threads",
    "obsidian-vault/Sources/Articles",
    "obsidian-vault/Sources/Papers",
    "logs",
)


def ensure_runtime_directories(project_root: Path) -> list[Path]:
    created: list[Path] = []
    for directory in PROJECT_DIRECTORIES:
        path = project_root / directory
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
    return created
