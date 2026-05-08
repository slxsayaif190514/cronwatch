"""Per-job alert quota enforcement — caps the number of alerts sent in a rolling time window."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.isoformat()


def _parse(s: str) -> datetime:
    return datetime.fromisoformat(s)


class QuotaEntry:
    def __init__(self, count: int, window_start: datetime) -> None:
        self.count = count
        self.window_start = window_start

    def to_dict(self) -> dict:
        return {"count": self.count, "window_start": _fmt(self.window_start)}

    @classmethod
    def from_dict(cls, d: dict) -> "QuotaEntry":
        return cls(count=d["count"], window_start=_parse(d["window_start"]))


class QuotaStore:
    def __init__(self, path: str, max_alerts: int = 5, window_hours: int = 1) -> None:
        self._path = Path(path)
        self.max_alerts = max_alerts
        self.window_hours = window_hours
        self._data: dict[str, QuotaEntry] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._data = {k: QuotaEntry.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self._path.write_text(json.dumps({k: v.to_dict() for k, v in self._data.items()}, indent=2))

    def _entry(self, job: str) -> Optional[QuotaEntry]:
        return self._data.get(job)

    def _reset_if_expired(self, job: str, now: datetime) -> None:
        entry = self._data.get(job)
        if entry is None:
            return
        if now - entry.window_start >= timedelta(hours=self.window_hours):
            del self._data[job]

    def is_quota_exceeded(self, job: str) -> bool:
        now = _utcnow()
        self._reset_if_expired(job, now)
        entry = self._data.get(job)
        if entry is None:
            return False
        return entry.count >= self.max_alerts

    def record_alert(self, job: str) -> int:
        now = _utcnow()
        self._reset_if_expired(job, now)
        entry = self._data.get(job)
        if entry is None:
            self._data[job] = QuotaEntry(count=1, window_start=now)
        else:
            entry.count += 1
        self._save()
        return self._data[job].count

    def reset(self, job: str) -> None:
        if job in self._data:
            del self._data[job]
            self._save()

    def get_count(self, job: str) -> int:
        now = _utcnow()
        self._reset_if_expired(job, now)
        entry = self._data.get(job)
        return entry.count if entry else 0

    def all_jobs(self) -> list[str]:
        now = _utcnow()
        for job in list(self._data):
            self._reset_if_expired(job, now)
        return sorted(self._data)
