"""Lockout store — tracks jobs that have been administratively locked out from alerting."""

import json
import os
from datetime import datetime, timezone
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


class LockoutEntry:
    def __init__(self, job_name: str, reason: str, locked_at: datetime, locked_by: str):
        self.job_name = job_name
        self.reason = reason
        self.locked_at = locked_at
        self.locked_by = locked_by

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "reason": self.reason,
            "locked_at": _fmt(self.locked_at),
            "locked_by": self.locked_by,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LockoutEntry":
        return cls(
            job_name=d["job_name"],
            reason=d["reason"],
            locked_at=_parse(d["locked_at"]),
            locked_by=d["locked_by"],
        )


class LockoutStore:
    def __init__(self, path: str):
        self._path = path
        self._entries: dict[str, LockoutEntry] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        with open(self._path) as f:
            raw = json.load(f)
        for item in raw:
            e = LockoutEntry.from_dict(item)
            self._entries[e.job_name] = e

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump([e.to_dict() for e in self._entries.values()], f, indent=2)

    def lock(self, job_name: str, reason: str, locked_by: str = "admin") -> LockoutEntry:
        entry = LockoutEntry(
            job_name=job_name,
            reason=reason,
            locked_at=_utcnow(),
            locked_by=locked_by,
        )
        self._entries[job_name] = entry
        self._save()
        return entry

    def unlock(self, job_name: str) -> bool:
        if job_name not in self._entries:
            return False
        del self._entries[job_name]
        self._save()
        return True

    def is_locked(self, job_name: str) -> bool:
        return job_name in self._entries

    def get(self, job_name: str) -> Optional[LockoutEntry]:
        return self._entries.get(job_name)

    def all(self) -> list[LockoutEntry]:
        return sorted(self._entries.values(), key=lambda e: e.job_name)
