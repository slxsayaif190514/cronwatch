"""Checkpoint store — tracks the last known-good run timestamp per job.

Useful for detecting when a job that previously succeeded has gone silent.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional

_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime(_FMT)


def _parse(s: str) -> datetime:
    return datetime.strptime(s, _FMT).replace(tzinfo=timezone.utc)


class CheckpointStore:
    """Persist the last-good-run timestamp for each job."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._data: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path) as fh:
                self._data = json.load(fh)

    def _save(self) -> None:
        with open(self._path, "w") as fh:
            json.dump(self._data, fh, indent=2)

    def set(self, job_name: str, dt: Optional[datetime] = None) -> datetime:
        """Record a checkpoint for *job_name*; defaults to now."""
        ts = dt or _utcnow()
        self._data[job_name] = _fmt(ts)
        self._save()
        return ts

    def get(self, job_name: str) -> Optional[datetime]:
        """Return the last checkpoint for *job_name*, or None."""
        raw = self._data.get(job_name)
        return _parse(raw) if raw else None

    def remove(self, job_name: str) -> bool:
        """Delete the checkpoint for *job_name*. Returns True if it existed."""
        if job_name in self._data:
            del self._data[job_name]
            self._save()
            return True
        return False

    def all(self) -> Dict[str, datetime]:
        """Return a dict of all job_name -> datetime checkpoints."""
        return {k: _parse(v) for k, v in self._data.items()}

    def age_seconds(self, job_name: str) -> Optional[float]:
        """Seconds since the last checkpoint, or None if never set."""
        cp = self.get(job_name)
        if cp is None:
            return None
        return (_utcnow() - cp).total_seconds()
