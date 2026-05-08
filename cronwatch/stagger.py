"""Stagger store — tracks per-job start-time offsets to avoid thundering herd."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


class StaggerEntry:
    def __init__(self, job_name: str, offset_seconds: int, reason: str = "", updated_at: Optional[datetime] = None):
        self.job_name = job_name
        self.offset_seconds = offset_seconds
        self.reason = reason
        self.updated_at = updated_at or _utcnow()

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "offset_seconds": self.offset_seconds,
            "reason": self.reason,
            "updated_at": _fmt(self.updated_at),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StaggerEntry":
        return cls(
            job_name=d["job_name"],
            offset_seconds=int(d["offset_seconds"]),
            reason=d.get("reason", ""),
            updated_at=_parse(d["updated_at"]),
        )


class StaggerStore:
    def __init__(self, path: str):
        self._path = path
        self._data: Dict[str, StaggerEntry] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        with open(self._path) as f:
            raw = json.load(f)
        for item in raw:
            e = StaggerEntry.from_dict(item)
            self._data[e.job_name] = e

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump([e.to_dict() for e in self._data.values()], f, indent=2)

    def get(self, job_name: str) -> Optional[StaggerEntry]:
        return self._data.get(job_name)

    def set(self, job_name: str, offset_seconds: int, reason: str = "") -> StaggerEntry:
        entry = StaggerEntry(job_name, offset_seconds, reason)
        self._data[job_name] = entry
        self._save()
        return entry

    def remove(self, job_name: str) -> bool:
        if job_name not in self._data:
            return False
        del self._data[job_name]
        self._save()
        return True

    def all(self) -> List[StaggerEntry]:
        return sorted(self._data.values(), key=lambda e: e.job_name)
