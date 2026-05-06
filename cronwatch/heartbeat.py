"""Heartbeat store — tracks periodic ping-ins from cron jobs.

Jobs can call the heartbeat endpoint (or CLI) to signal they are alive.
The monitor can then detect jobs that have gone silent beyond a threshold.
"""

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


class HeartbeatStore:
    """Persist the last heartbeat timestamp for each job."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._data: Dict[str, str] = {}
        self._load()

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path) as fh:
                self._data = json.load(fh)

    def _save(self) -> None:
        with open(self._path, "w") as fh:
            json.dump(self._data, fh, indent=2)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def ping(self, job_name: str, at: Optional[datetime] = None) -> datetime:
        """Record a heartbeat for *job_name*; returns the recorded timestamp."""
        ts = at if at is not None else _utcnow()
        self._data[job_name] = _fmt(ts)
        self._save()
        return ts

    def last_ping(self, job_name: str) -> Optional[datetime]:
        """Return the last heartbeat time for *job_name*, or None."""
        raw = self._data.get(job_name)
        return _parse(raw) if raw else None

    def is_stale(self, job_name: str, max_age_seconds: float) -> bool:
        """Return True if the job has not pinged within *max_age_seconds*."""
        last = self.last_ping(job_name)
        if last is None:
            return True
        return (_utcnow() - last).total_seconds() > max_age_seconds

    def all_jobs(self) -> List[str]:
        """Return sorted list of job names that have ever pinged."""
        return sorted(self._data.keys())

    def remove(self, job_name: str) -> bool:
        """Delete heartbeat record for *job_name*. Returns True if it existed."""
        if job_name in self._data:
            del self._data[job_name]
            self._save()
            return True
        return False
