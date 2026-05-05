"""Lightweight in-process metrics collection for cronwatch."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


def _utcnow() -> float:
    return time.time()


@dataclass
class JobMetrics:
    job_name: str
    total_runs: int = 0
    success_runs: int = 0
    failure_runs: int = 0
    total_duration_s: float = 0.0
    min_duration_s: Optional[float] = None
    max_duration_s: Optional[float] = None

    def record(self, success: bool, duration_s: float) -> None:
        self.total_runs += 1
        self.total_duration_s += duration_s
        if success:
            self.success_runs += 1
        else:
            self.failure_runs += 1
        if self.min_duration_s is None or duration_s < self.min_duration_s:
            self.min_duration_s = duration_s
        if self.max_duration_s is None or duration_s > self.max_duration_s:
            self.max_duration_s = duration_s

    @property
    def avg_duration_s(self) -> Optional[float]:
        if self.total_runs == 0:
            return None
        return self.total_duration_s / self.total_runs

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "total_runs": self.total_runs,
            "success_runs": self.success_runs,
            "failure_runs": self.failure_runs,
            "total_duration_s": self.total_duration_s,
            "min_duration_s": self.min_duration_s,
            "max_duration_s": self.max_duration_s,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "JobMetrics":
        m = cls(job_name=d["job_name"])
        m.total_runs = d.get("total_runs", 0)
        m.success_runs = d.get("success_runs", 0)
        m.failure_runs = d.get("failure_runs", 0)
        m.total_duration_s = d.get("total_duration_s", 0.0)
        m.min_duration_s = d.get("min_duration_s")
        m.max_duration_s = d.get("max_duration_s")
        return m


class MetricsStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: Dict[str, JobMetrics] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._data = {k: JobMetrics.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self._path.write_text(json.dumps({k: v.to_dict() for k, v in self._data.items()}, indent=2))

    def get(self, job_name: str) -> JobMetrics:
        if job_name not in self._data:
            self._data[job_name] = JobMetrics(job_name=job_name)
        return self._data[job_name]

    def record(self, job_name: str, success: bool, duration_s: float) -> JobMetrics:
        m = self.get(job_name)
        m.record(success, duration_s)
        self._save()
        return m

    def all_metrics(self) -> List[JobMetrics]:
        return list(self._data.values())

    def reset(self, job_name: str) -> None:
        self._data.pop(job_name, None)
        self._save()
