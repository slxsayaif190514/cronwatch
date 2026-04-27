"""Persistent run history log for cron jobs."""

import json
import os
from datetime import datetime
from typing import List, Optional

DT_FORMAT = "%Y-%m-%dT%H:%M:%S"


def _parse_dt(s: str) -> datetime:
    return datetime.strptime(s, DT_FORMAT)


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime(DT_FORMAT)


class RunRecord:
    def __init__(self, job_name: str, started_at: datetime, success: bool, duration_s: float):
        self.job_name = job_name
        self.started_at = started_at
        self.success = success
        self.duration_s = duration_s

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "started_at": _fmt_dt(self.started_at),
            "success": self.success,
            "duration_s": self.duration_s,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RunRecord":
        return cls(
            job_name=d["job_name"],
            started_at=_parse_dt(d["started_at"]),
            success=d["success"],
            duration_s=d["duration_s"],
        )


class JobHistory:
    def __init__(self, path: str, max_records: int = 500):
        self.path = path
        self.max_records = max_records
        self._records: List[RunRecord] = []
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            self._records = []
            return
        with open(self.path) as f:
            data = json.load(f)
        self._records = [RunRecord.from_dict(r) for r in data]

    def _save(self):
        with open(self.path, "w") as f:
            json.dump([r.to_dict() for r in self._records], f, indent=2)

    def record(self, record: RunRecord):
        self._records.append(record)
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records :]
        self._save()

    def get_records(self, job_name: str) -> List[RunRecord]:
        return [r for r in self._records if r.job_name == job_name]

    def last_success(self, job_name: str) -> Optional[RunRecord]:
        matches = [r for r in self.get_records(job_name) if r.success]
        return matches[-1] if matches else None

    def average_duration(self, job_name: str) -> Optional[float]:
        durations = [r.duration_s for r in self.get_records(job_name) if r.success]
        if not durations:
            return None
        return sum(durations) / len(durations)
