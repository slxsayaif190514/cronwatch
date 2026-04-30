"""Job dependency tracking — ensures jobs run in expected order."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


@dataclass
class DependencyState:
    job_name: str
    depends_on: List[str] = field(default_factory=list)
    last_satisfied: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "depends_on": self.depends_on,
            "last_satisfied": _fmt(self.last_satisfied) if self.last_satisfied else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DependencyState":
        return cls(
            job_name=d["job_name"],
            depends_on=d.get("depends_on", []),
            last_satisfied=_parse(d["last_satisfied"]) if d.get("last_satisfied") else None,
        )


class DependencyStore:
    def __init__(self, path: str) -> None:
        self._path = path
        self._data: Dict[str, DependencyState] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path) as f:
                raw = json.load(f)
            self._data = {k: DependencyState.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump({k: v.to_dict() for k, v in self._data.items()}, f, indent=2)

    def set_dependencies(self, job_name: str, depends_on: List[str]) -> None:
        state = self._data.get(job_name, DependencyState(job_name=job_name))
        state.depends_on = depends_on
        self._data[job_name] = state
        self._save()

    def mark_satisfied(self, job_name: str) -> None:
        state = self._data.get(job_name, DependencyState(job_name=job_name))
        state.last_satisfied = _utcnow()
        self._data[job_name] = state
        self._save()

    def get(self, job_name: str) -> Optional[DependencyState]:
        return self._data.get(job_name)

    def dependencies_met(self, job_name: str, since: datetime) -> bool:
        """Return True if all dependencies ran successfully since `since`."""
        state = self._data.get(job_name)
        if not state or not state.depends_on:
            return True
        for dep in state.depends_on:
            dep_state = self._data.get(dep)
            if dep_state is None or dep_state.last_satisfied is None:
                return False
            if dep_state.last_satisfied < since:
                return False
        return True
