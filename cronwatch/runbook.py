"""Runbook links — attach remediation URLs and notes to jobs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional


def _utcnow() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class RunbookEntry:
    job_name: str
    url: str
    notes: str
    updated_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "RunbookEntry":
        return RunbookEntry(
            job_name=d["job_name"],
            url=d.get("url", ""),
            notes=d.get("notes", ""),
            updated_at=d.get("updated_at", ""),
        )


class RunbookStore:
    def __init__(self, path: str) -> None:
        self._path = path
        self._data: dict[str, RunbookEntry] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        with open(self._path) as f:
            raw = json.load(f)
        self._data = {k: RunbookEntry.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump({k: v.to_dict() for k, v in self._data.items()}, f, indent=2)

    def set(self, job_name: str, url: str, notes: str = "") -> RunbookEntry:
        entry = RunbookEntry(job_name=job_name, url=url, notes=notes, updated_at=_utcnow())
        self._data[job_name] = entry
        self._save()
        return entry

    def get(self, job_name: str) -> Optional[RunbookEntry]:
        return self._data.get(job_name)

    def remove(self, job_name: str) -> bool:
        if job_name not in self._data:
            return False
        del self._data[job_name]
        self._save()
        return True

    def all(self) -> list[RunbookEntry]:
        return sorted(self._data.values(), key=lambda e: e.job_name)
