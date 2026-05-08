"""Exponential backoff store for alert retry intervals."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_DEFAULT_BASE = 60        # seconds
_DEFAULT_MAX  = 3600      # seconds
_DEFAULT_FACTOR = 2.0


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


class BackoffEntry:
    def __init__(self, job: str, attempt: int = 0, last_alert: Optional[datetime] = None):
        self.job = job
        self.attempt = attempt
        self.last_alert = last_alert

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "attempt": self.attempt,
            "last_alert": _fmt(self.last_alert) if self.last_alert else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BackoffEntry":
        return cls(
            job=d["job"],
            attempt=d.get("attempt", 0),
            last_alert=_parse(d["last_alert"]) if d.get("last_alert") else None,
        )


class BackoffStore:
    def __init__(self, path: str, base_s: int = _DEFAULT_BASE,
                 max_s: int = _DEFAULT_MAX, factor: float = _DEFAULT_FACTOR):
        self._path = Path(path)
        self.base_s = base_s
        self.max_s = max_s
        self.factor = factor
        self._data: dict[str, BackoffEntry] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._data = {k: BackoffEntry.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self._path.write_text(json.dumps({k: v.to_dict() for k, v in self._data.items()}, indent=2))

    def get(self, job: str) -> BackoffEntry:
        return self._data.get(job, BackoffEntry(job))

    def interval_s(self, job: str) -> int:
        entry = self.get(job)
        raw = self.base_s * (self.factor ** entry.attempt)
        return int(min(raw, self.max_s))

    def is_ready(self, job: str) -> bool:
        entry = self.get(job)
        if entry.last_alert is None:
            return True
        elapsed = (_utcnow() - entry.last_alert).total_seconds()
        return elapsed >= self.interval_s(job)

    def record_alert(self, job: str) -> BackoffEntry:
        entry = self.get(job)
        entry.attempt += 1
        entry.last_alert = _utcnow()
        self._data[job] = entry
        self._save()
        return entry

    def reset(self, job: str) -> None:
        if job in self._data:
            del self._data[job]
            self._save()
