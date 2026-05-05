"""Baseline duration tracking — learns expected run durations from history."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class BaselineStats:
    job_name: str
    sample_count: int
    avg_duration_s: float
    stddev_s: float
    updated_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BaselineStats":
        return cls(**d)

    def upper_bound(self, sigma: float = 2.0) -> float:
        """Return avg + sigma * stddev as the alert threshold."""
        return self.avg_duration_s + sigma * self.stddev_s


class BaselineStore:
    def __init__(self, path: str) -> None:
        self._path = path
        self._data: dict[str, BaselineStats] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        with open(self._path) as f:
            raw = json.load(f)
        self._data = {k: BaselineStats.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump({k: v.to_dict() for k, v in self._data.items()}, f, indent=2)

    def get(self, job_name: str) -> Optional[BaselineStats]:
        return self._data.get(job_name)

    def update(self, job_name: str, duration_s: float) -> BaselineStats:
        """Incrementally update the running mean and variance (Welford's method)."""
        existing = self._data.get(job_name)
        if existing is None:
            stats = BaselineStats(
                job_name=job_name,
                sample_count=1,
                avg_duration_s=duration_s,
                stddev_s=0.0,
                updated_at=_utcnow().isoformat(),
            )
        else:
            n = existing.sample_count + 1
            delta = duration_s - existing.avg_duration_s
            new_avg = existing.avg_duration_s + delta / n
            delta2 = duration_s - new_avg
            # running sum of squared deviations stored via stddev approximation
            prev_m2 = (existing.stddev_s ** 2) * (existing.sample_count - 1) if existing.sample_count > 1 else 0.0
            new_m2 = prev_m2 + delta * delta2
            new_stddev = (new_m2 / (n - 1)) ** 0.5 if n > 1 else 0.0
            stats = BaselineStats(
                job_name=job_name,
                sample_count=n,
                avg_duration_s=round(new_avg, 4),
                stddev_s=round(new_stddev, 4),
                updated_at=_utcnow().isoformat(),
            )
        self._data[job_name] = stats
        self._save()
        return stats

    def reset(self, job_name: str) -> bool:
        if job_name in self._data:
            del self._data[job_name]
            self._save()
            return True
        return False

    def all_stats(self) -> list[BaselineStats]:
        return list(self._data.values())
