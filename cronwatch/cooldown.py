"""Per-job alert cooldown store — tracks when the last alert was sent
and whether a new alert is allowed based on a configurable cooldown period."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime(_FMT)


def _parse(s: str) -> datetime:
    return datetime.strptime(s, _FMT).replace(tzinfo=timezone.utc)


class CooldownStore:
    """Persist last-alert timestamps and enforce per-job cooldown windows."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._data: dict[str, str] = self._load()

    def _load(self) -> dict[str, str]:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._data, indent=2))

    def record_alert(self, job_name: str) -> datetime:
        """Record that an alert was just sent for *job_name*."""
        now = _utcnow()
        self._data[job_name] = _fmt(now)
        self._save()
        return now

    def last_alert(self, job_name: str) -> Optional[datetime]:
        """Return the datetime of the last alert for *job_name*, or None."""
        raw = self._data.get(job_name)
        return _parse(raw) if raw else None

    def is_cooled_down(self, job_name: str, cooldown_seconds: int) -> bool:
        """Return True if enough time has passed since the last alert."""
        last = self.last_alert(job_name)
        if last is None:
            return True
        elapsed = (_utcnow() - last).total_seconds()
        return elapsed >= cooldown_seconds

    def reset(self, job_name: str) -> None:
        """Remove the cooldown record for *job_name*."""
        self._data.pop(job_name, None)
        self._save()

    def all_jobs(self) -> list[str]:
        return sorted(self._data.keys())
