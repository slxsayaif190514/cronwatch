"""Per-job alert rate limiting with sliding window counters."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.isoformat()


def _parse(s: str) -> datetime:
    return datetime.fromisoformat(s)


class RateLimitStore:
    """Tracks alert timestamps per job to enforce rate limits."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._data: Dict[str, List[str]] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path) as f:
                self._data = json.load(f)

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    def record_alert(self, job_name: str) -> None:
        """Record that an alert was sent for *job_name* right now."""
        timestamps = self._data.setdefault(job_name, [])
        timestamps.append(_fmt(_utcnow()))
        self._save()

    def prune(self, job_name: str, window_seconds: int) -> None:
        """Remove timestamps older than *window_seconds* for *job_name*."""
        cutoff = _utcnow().timestamp() - window_seconds
        kept = [
            ts for ts in self._data.get(job_name, [])
            if _parse(ts).timestamp() >= cutoff
        ]
        self._data[job_name] = kept
        self._save()

    def alert_count(self, job_name: str, window_seconds: int) -> int:
        """Return the number of alerts sent within the sliding window."""
        self.prune(job_name, window_seconds)
        return len(self._data.get(job_name, []))

    def is_rate_limited(
        self, job_name: str, max_alerts: int, window_seconds: int
    ) -> bool:
        """Return True if *job_name* has hit *max_alerts* within *window_seconds*."""
        return self.alert_count(job_name, window_seconds) >= max_alerts

    def reset(self, job_name: str) -> None:
        """Clear all recorded alert timestamps for *job_name*."""
        self._data.pop(job_name, None)
        self._save()
