"""Circuit breaker for job alerting — stops firing alerts when a job
is persistently broken, to avoid notification fatigue."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime(_FMT)


def _parse(s: str) -> datetime:
    return datetime.strptime(s, _FMT).replace(tzinfo=timezone.utc)


class CircuitEntry:
    def __init__(self, job: str, failures: int, opened_at: Optional[datetime], half_open: bool):
        self.job = job
        self.failures = failures
        self.opened_at = opened_at
        self.half_open = half_open

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "failures": self.failures,
            "opened_at": _fmt(self.opened_at) if self.opened_at else None,
            "half_open": self.half_open,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CircuitEntry":
        return cls(
            job=d["job"],
            failures=d["failures"],
            opened_at=_parse(d["opened_at"]) if d.get("opened_at") else None,
            half_open=d.get("half_open", False),
        )


class CircuitStore:
    def __init__(self, path: str, threshold: int = 5, reset_after_s: int = 3600):
        self._path = Path(path)
        self.threshold = threshold
        self.reset_after_s = reset_after_s
        self._data: dict[str, CircuitEntry] = {}
        self._load()

    def _load(self):
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._data = {k: CircuitEntry.from_dict(v) for k, v in raw.items()}

    def _save(self):
        self._path.write_text(json.dumps({k: v.to_dict() for k, v in self._data.items()}, indent=2))

    def get(self, job: str) -> CircuitEntry:
        return self._data.get(job, CircuitEntry(job, 0, None, False))

    def record_failure(self, job: str) -> CircuitEntry:
        entry = self.get(job)
        entry.failures += 1
        if entry.failures >= self.threshold and entry.opened_at is None:
            entry.opened_at = _utcnow()
        entry.half_open = False
        self._data[job] = entry
        self._save()
        return entry

    def record_success(self, job: str):
        if job in self._data:
            del self._data[job]
            self._save()

    def is_open(self, job: str) -> bool:
        entry = self.get(job)
        if entry.opened_at is None:
            return False
        elapsed = (_utcnow() - entry.opened_at).total_seconds()
        if elapsed >= self.reset_after_s:
            entry.half_open = True
            self._data[job] = entry
            self._save()
            return False
        return entry.failures >= self.threshold

    def reset(self, job: str):
        self.record_success(job)
