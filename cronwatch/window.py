"""Execution window tracking: record and query whether a job ran within its expected window."""

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


class WindowEntry:
    def __init__(self, job_name: str, window_start: datetime, window_end: datetime, ran: bool = False):
        self.job_name = job_name
        self.window_start = window_start
        self.window_end = window_end
        self.ran = ran

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "window_start": _fmt(self.window_start),
            "window_end": _fmt(self.window_end),
            "ran": self.ran,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WindowEntry":
        return cls(
            job_name=d["job_name"],
            window_start=_parse(d["window_start"]),
            window_end=_parse(d["window_end"]),
            ran=d.get("ran", False),
        )


class WindowStore:
    def __init__(self, path: str) -> None:
        self._path = path
        self._entries: List[WindowEntry] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        with open(self._path) as f:
            raw = json.load(f)
        self._entries = [WindowEntry.from_dict(r) for r in raw]

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump([e.to_dict() for e in self._entries], f, indent=2)

    def add_window(self, job_name: str, window_start: datetime, window_end: datetime) -> WindowEntry:
        entry = WindowEntry(job_name, window_start, window_end, ran=False)
        self._entries.append(entry)
        self._save()
        return entry

    def mark_ran(self, job_name: str, at: Optional[datetime] = None) -> bool:
        """Mark the most recent open window for job_name as ran. Returns True if found."""
        ts = at or _utcnow()
        for entry in reversed(self._entries):
            if entry.job_name == job_name and entry.window_start <= ts <= entry.window_end and not entry.ran:
                entry.ran = True
                self._save()
                return True
        return False

    def missed_windows(self, job_name: str, before: Optional[datetime] = None) -> List[WindowEntry]:
        """Return windows that closed without a run."""
        cutoff = before or _utcnow()
        return [
            e for e in self._entries
            if e.job_name == job_name and not e.ran and e.window_end < cutoff
        ]

    def get_windows(self, job_name: str) -> List[WindowEntry]:
        return [e for e in self._entries if e.job_name == job_name]

    def clear(self, job_name: str) -> int:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.job_name != job_name]
        self._save()
        return before - len(self._entries)
