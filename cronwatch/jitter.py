"""Jitter detection: flag jobs whose actual run times drift significantly
from their expected schedule over a rolling window."""
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


class JitterStore:
    """Persists per-job jitter samples (offset in seconds from expected run)."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._data: Dict[str, List[float]] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path) as fh:
                self._data = json.load(fh)

    def _save(self) -> None:
        with open(self._path, "w") as fh:
            json.dump(self._data, fh, indent=2)

    def record(self, job_name: str, offset_s: float, max_samples: int = 100) -> None:
        """Record a jitter offset (seconds) for *job_name*."""
        samples = self._data.setdefault(job_name, [])
        samples.append(offset_s)
        if len(samples) > max_samples:
            self._data[job_name] = samples[-max_samples:]
        self._save()

    def get_samples(self, job_name: str) -> List[float]:
        return list(self._data.get(job_name, []))

    def avg_jitter(self, job_name: str) -> Optional[float]:
        samples = self.get_samples(job_name)
        if not samples:
            return None
        return sum(abs(s) for s in samples) / len(samples)

    def is_high_jitter(self, job_name: str, threshold_s: float = 60.0) -> bool:
        avg = self.avg_jitter(job_name)
        return avg is not None and avg > threshold_s

    def reset(self, job_name: str) -> None:
        self._data.pop(job_name, None)
        self._save()

    def all_jobs(self) -> List[str]:
        return sorted(self._data.keys())
