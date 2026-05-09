"""Burst detection: flag jobs that run far more frequently than expected."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

_DT_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime(_DT_FMT)


def _parse(s: str) -> datetime:
    return datetime.strptime(s, _DT_FMT).replace(tzinfo=timezone.utc)


class BurstEntry:
    def __init__(self, job: str, timestamps: List[datetime]):
        self.job = job
        self.timestamps = timestamps

    def to_dict(self) -> dict:
        return {"job": self.job, "timestamps": [_fmt(t) for t in self.timestamps]}

    @classmethod
    def from_dict(cls, d: dict) -> "BurstEntry":
        return cls(d["job"], [_parse(t) for t in d.get("timestamps", [])])


class BurstStore:
    def __init__(self, path: str):
        self._path = path
        self._data: Dict[str, BurstEntry] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        with open(self._path) as f:
            raw = json.load(f)
        for item in raw.get("entries", []):
            e = BurstEntry.from_dict(item)
            self._data[e.job] = e

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump({"entries": [e.to_dict() for e in self._data.values()]}, f, indent=2)

    def record(self, job: str, window_seconds: int = 3600) -> None:
        """Record a run timestamp, pruning entries outside the window."""
        now = _utcnow()
        entry = self._data.get(job, BurstEntry(job, []))
        cutoff = now.timestamp() - window_seconds
        entry.timestamps = [t for t in entry.timestamps if t.timestamp() >= cutoff]
        entry.timestamps.append(now)
        self._data[job] = entry
        self._save()

    def get_count(self, job: str, window_seconds: int = 3600) -> int:
        """Return how many runs occurred within the window."""
        now = _utcnow()
        entry = self._data.get(job)
        if entry is None:
            return 0
        cutoff = now.timestamp() - window_seconds
        return sum(1 for t in entry.timestamps if t.timestamp() >= cutoff)

    def is_bursting(self, job: str, max_runs: int, window_seconds: int = 3600) -> bool:
        return self.get_count(job, window_seconds) > max_runs

    def reset(self, job: str) -> None:
        self._data.pop(job, None)
        self._save()

    def all_jobs(self) -> List[str]:
        return sorted(self._data.keys())
