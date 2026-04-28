"""Escalation policy: track repeated alert failures and escalate to a secondary channel."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional

_DT_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime(_DT_FMT)


def _parse(s: str) -> datetime:
    return datetime.strptime(s, _DT_FMT).replace(tzinfo=timezone.utc)


class EscalationStore:
    """Persists per-job alert counts so we can escalate after N consecutive alerts."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._data: Dict[str, dict] = self._load()

    def _load(self) -> Dict[str, dict]:
        if not os.path.exists(self._path):
            return {}
        with open(self._path) as fh:
            try:
                return json.load(fh)
            except (json.JSONDecodeError, ValueError):
                return {}

    def _save(self) -> None:
        with open(self._path, "w") as fh:
            json.dump(self._data, fh)

    def record_alert(self, job_name: str) -> int:
        """Increment alert counter for job and return the new count."""
        entry = self._data.get(job_name, {"count": 0, "first_alert": _fmt(_utcnow())})
        entry["count"] = entry.get("count", 0) + 1
        entry["last_alert"] = _fmt(_utcnow())
        self._data[job_name] = entry
        self._save()
        return entry["count"]

    def reset(self, job_name: str) -> None:
        """Reset counter after a successful run."""
        if job_name in self._data:
            del self._data[job_name]
            self._save()

    def get_count(self, job_name: str) -> int:
        return self._data.get(job_name, {}).get("count", 0)

    def should_escalate(self, job_name: str, threshold: int) -> bool:
        """Return True when alert count has reached the escalation threshold."""
        if threshold <= 0:
            return False
        return self.get_count(job_name) >= threshold
