"""Per-job alert throttling with configurable burst limits."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.isoformat()


def _parse(s: str) -> datetime:
    return datetime.fromisoformat(s)


class ThrottleEntry:
    def __init__(self, count: int, window_start: datetime, last_alert: Optional[datetime]):
        self.count = count
        self.window_start = window_start
        self.last_alert = last_alert

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "window_start": _fmt(self.window_start),
            "last_alert": _fmt(self.last_alert) if self.last_alert else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ThrottleEntry":
        return cls(
            count=d["count"],
            window_start=_parse(d["window_start"]),
            last_alert=_parse(d["last_alert"]) if d.get("last_alert") else None,
        )


class ThrottleStore:
    """Tracks per-job alert burst counts within a rolling time window."""

    def __init__(self, path: str, window_seconds: int = 3600, max_burst: int = 5):
        self.path = path
        self.window_seconds = window_seconds
        self.max_burst = max_burst
        self._data: Dict[str, ThrottleEntry] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            with open(self.path) as f:
                raw = json.load(f)
            self._data = {k: ThrottleEntry.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        with open(self.path, "w") as f:
            json.dump({k: v.to_dict() for k, v in self._data.items()}, f, indent=2)

    def _get_or_create(self, job: str) -> ThrottleEntry:
        now = _utcnow()
        entry = self._data.get(job)
        if entry is None:
            entry = ThrottleEntry(count=0, window_start=now, last_alert=None)
            self._data[job] = entry
        elapsed = (now - entry.window_start).total_seconds()
        if elapsed >= self.window_seconds:
            entry.count = 0
            entry.window_start = now
        return entry

    def is_throttled(self, job: str) -> bool:
        entry = self._get_or_create(job)
        return entry.count >= self.max_burst

    def record_alert(self, job: str) -> ThrottleEntry:
        entry = self._get_or_create(job)
        entry.count += 1
        entry.last_alert = _utcnow()
        self._save()
        return entry

    def reset(self, job: str) -> None:
        self._data.pop(job, None)
        self._save()

    def get_entry(self, job: str) -> Optional[ThrottleEntry]:
        return self._data.get(job)
