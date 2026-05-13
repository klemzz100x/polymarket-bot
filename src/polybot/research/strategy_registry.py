from dataclasses import asdict, dataclass, field
from datetime import datetime
from polybot.core.compat import UTC
import json
from pathlib import Path
from typing import Any

from polybot.research.obsidian_mining.strategy_candidate import (
    CandidateStatus,
    StrategyCandidate,
)


PRIORITY_SCORE = {"high": 3, "medium": 2, "low": 1}
DIFFICULTY_PENALTY = {"low": 0, "medium": 1, "high": 2}


@dataclass(frozen=True, slots=True)
class StrategyCandidateRecord:
    candidate: StrategyCandidate
    status: CandidateStatus = CandidateStatus.NEW
    backtest_results: list[str] = field(default_factory=list)
    paper_trading_results: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def candidate_id(self) -> str:
        return self.candidate.candidate_id

    @property
    def rank_score(self) -> int:
        priority = PRIORITY_SCORE.get(self.candidate.priority, 0)
        difficulty = DIFFICULTY_PENALTY.get(self.candidate.implementation_difficulty, 1)
        status_boost = 2 if self.status == CandidateStatus.PROMISING else 0
        return priority * 10 - difficulty + status_boost

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(
            {
                "candidate": self.candidate.to_dict(),
                "status": self.status.value,
                "backtest_results": self.backtest_results,
                "paper_trading_results": self.paper_trading_results,
                "notes": self.notes,
                "updated_at": self.updated_at,
                "rank_score": self.rank_score,
            }
        )


class StrategyCandidateRegistry:
    def __init__(self, path: Path) -> None:
        self.path = path

    def list_candidates(self, status: CandidateStatus | None = None) -> list[StrategyCandidateRecord]:
        records = self._load()
        if status is None:
            return records
        return [record for record in records if record.status == status]

    def rank_candidates(self) -> list[StrategyCandidateRecord]:
        return sorted(
            self._load(),
            key=lambda record: (-record.rank_score, record.candidate.edge_family.value, record.candidate.name),
        )

    def upsert_candidate(self, candidate: StrategyCandidate) -> StrategyCandidateRecord:
        records = self._load()
        existing = next((record for record in records if record.candidate_id == candidate.candidate_id), None)
        if existing:
            updated = StrategyCandidateRecord(
                candidate=candidate,
                status=existing.status,
                backtest_results=existing.backtest_results,
                paper_trading_results=existing.paper_trading_results,
                notes=existing.notes,
            )
            records = [updated if item.candidate_id == candidate.candidate_id else item for item in records]
        else:
            updated = StrategyCandidateRecord(candidate=candidate)
            records.append(updated)
        self._save(records)
        return updated

    def upsert_many(self, candidates: list[StrategyCandidate]) -> list[StrategyCandidateRecord]:
        if not candidates:
            self._save(self._load())
            return []
        records = [self.upsert_candidate(candidate) for candidate in candidates]
        return records

    def mark_as_tested(self, candidate_id: str, *, note: str | None = None) -> StrategyCandidateRecord:
        return self._update_status(candidate_id, CandidateStatus.TESTED, note=note)

    def mark_as_rejected(self, candidate_id: str, *, note: str | None = None) -> StrategyCandidateRecord:
        return self._update_status(candidate_id, CandidateStatus.REJECTED, note=note)

    def mark_as_promising(self, candidate_id: str, *, note: str | None = None) -> StrategyCandidateRecord:
        return self._update_status(candidate_id, CandidateStatus.PROMISING, note=note)

    def link_candidate_to_backtest(self, candidate_id: str, result_ref: str) -> StrategyCandidateRecord:
        return self._append_link(candidate_id, "backtest_results", result_ref)

    def link_candidate_to_paper_trading(self, candidate_id: str, result_ref: str) -> StrategyCandidateRecord:
        return self._append_link(candidate_id, "paper_trading_results", result_ref)

    def _update_status(
        self,
        candidate_id: str,
        status: CandidateStatus,
        *,
        note: str | None = None,
    ) -> StrategyCandidateRecord:
        records = self._load()
        updated_records: list[StrategyCandidateRecord] = []
        target: StrategyCandidateRecord | None = None
        for record in records:
            if record.candidate_id != candidate_id:
                updated_records.append(record)
                continue
            notes = [*record.notes, note] if note else record.notes
            target = StrategyCandidateRecord(
                candidate=record.candidate,
                status=status,
                backtest_results=record.backtest_results,
                paper_trading_results=record.paper_trading_results,
                notes=notes,
            )
            updated_records.append(target)
        if target is None:
            raise KeyError(f"Unknown strategy candidate: {candidate_id}")
        self._save(updated_records)
        return target

    def _append_link(
        self,
        candidate_id: str,
        field_name: str,
        result_ref: str,
    ) -> StrategyCandidateRecord:
        records = self._load()
        updated_records: list[StrategyCandidateRecord] = []
        target: StrategyCandidateRecord | None = None
        for record in records:
            if record.candidate_id != candidate_id:
                updated_records.append(record)
                continue
            backtests = list(record.backtest_results)
            paper = list(record.paper_trading_results)
            if field_name == "backtest_results" and result_ref not in backtests:
                backtests.append(result_ref)
            if field_name == "paper_trading_results" and result_ref not in paper:
                paper.append(result_ref)
            target = StrategyCandidateRecord(
                candidate=record.candidate,
                status=record.status,
                backtest_results=backtests,
                paper_trading_results=paper,
                notes=record.notes,
            )
            updated_records.append(target)
        if target is None:
            raise KeyError(f"Unknown strategy candidate: {candidate_id}")
        self._save(updated_records)
        return target

    def _load(self) -> list[StrategyCandidateRecord]:
        if not self.path.exists():
            return []
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return [_record_from_dict(item) for item in raw.get("records", [])]

    def _save(self, records: list[StrategyCandidateRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": datetime.now(UTC).isoformat(),
            "records": [record.to_dict() for record in self.rank_records(records)],
        }
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def rank_records(records: list[StrategyCandidateRecord]) -> list[StrategyCandidateRecord]:
        return sorted(
            records,
            key=lambda record: (-record.rank_score, record.candidate.edge_family.value, record.candidate.name),
        )


def _record_from_dict(data: dict[str, Any]) -> StrategyCandidateRecord:
    from polybot.research.obsidian_mining.strategy_candidate import EdgeFamily

    raw_candidate = data["candidate"]
    candidate = StrategyCandidate(
        name=raw_candidate["name"],
        source_obsidian_path=raw_candidate["source_obsidian_path"],
        source_title=raw_candidate["source_title"],
        source_url=raw_candidate.get("source_url") or None,
        summary=raw_candidate["summary"],
        hypothesis=raw_candidate["hypothesis"],
        edge_family=EdgeFamily(raw_candidate["edge_family"]),
        required_data=list(raw_candidate["required_data"]),
        metrics_to_measure=list(raw_candidate["metrics_to_measure"]),
        testable_signal=raw_candidate["testable_signal"],
        backtest_design=raw_candidate["backtest_design"],
        main_risk=raw_candidate["main_risk"],
        implementation_difficulty=raw_candidate["implementation_difficulty"],
        priority=raw_candidate["priority"],
        next_action=raw_candidate["next_action"],
        evidence=list(raw_candidate.get("evidence", [])),
    )
    return StrategyCandidateRecord(
        candidate=candidate,
        status=CandidateStatus(data.get("status", CandidateStatus.NEW.value)),
        backtest_results=list(data.get("backtest_results", [])),
        paper_trading_results=list(data.get("paper_trading_results", [])),
        notes=list(data.get("notes", [])),
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
