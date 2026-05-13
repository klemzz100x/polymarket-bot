from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResearchTask:
    task_id: str
    objective: str
    source_refs: list[str]


class ResearchOrchestrator:
    def plan(self, task: ResearchTask) -> list[str]:
        return [
            f"Collect sources for {task.task_id}",
            "Extract claims and hypotheses",
            "Generate clean Obsidian note",
            "Link note to strategy or backtest if relevant",
        ]

