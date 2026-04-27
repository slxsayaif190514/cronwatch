"""Silence windows — suppress alerts for specific jobs during scheduled maintenance."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def _fmt(dt: datetime) -> str:
    return dt.isoformat()


class SilenceWindow:
    def __init__(self, job_name: str, start: datetime, end: datetime, reason: str = ""):
        self.job_name = job_name
        self.start = start
        self.end = end
        self.reason = reason

    def is_active(self, at: Optional[datetime] = None) -> bool:
        now = at or _utcnow()
        return self.start <= now <= self.end

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "start": _fmt(self.start),
            "end": _fmt(self.end),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SilenceWindow":
        return cls(
            job_name=data["job_name"],
            start=_parse(data["start"]),
            end=_parse(data["end"]),
            reason=data.get("reason", ""),
        )


class SilenceStore:
    def __init__(self, path: str):
        self._path = path
        self._windows: List[SilenceWindow] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        with open(self._path) as f:
            raw = json.load(f)
        self._windows = [SilenceWindow.from_dict(d) for d in raw]

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump([w.to_dict() for w in self._windows], f, indent=2)

    def add(self, window: SilenceWindow) -> None:
        self._windows.append(window)
        self._save()

    def remove_expired(self) -> int:
        now = _utcnow()
        before = len(self._windows)
        self._windows = [w for w in self._windows if w.end > now]
        self._save()
        return before - len(self._windows)

    def is_silenced(self, job_name: str, at: Optional[datetime] = None) -> bool:
        return any(
            w.job_name == job_name and w.is_active(at)
            for w in self._windows
        )

    def all_windows(self) -> List[SilenceWindow]:
        return list(self._windows)
