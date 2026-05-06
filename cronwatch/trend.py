"""Trend analysis: detect if job durations are drifting over time."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional

_TREND_VERSION = 1


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


@dataclass
class TrendPoint:
    recorded_at: str
    duration_s: float

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TrendPoint":
        return cls(**d)


class TrendStore:
    def __init__(self, path: str, window: int = 20) -> None:
        self._path = path
        self._window = window
        self._data: dict = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self._path):
            return {}
        with open(self._path) as f:
            return json.load(f)

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    def record(self, job_name: str, duration_s: float) -> None:
        points = self._data.get(job_name, [])
        points.append(TrendPoint(_fmt(_utcnow()), duration_s).to_dict())
        self._data[job_name] = points[-self._window :]
        self._save()

    def get_points(self, job_name: str) -> List[TrendPoint]:
        return [TrendPoint.from_dict(d) for d in self._data.get(job_name, [])]

    def slope(self, job_name: str) -> Optional[float]:
        """Return simple linear regression slope (seconds per run). None if <2 points."""
        pts = self.get_points(job_name)
        if len(pts) < 2:
            return None
        n = len(pts)
        xs = list(range(n))
        ys = [p.duration_s for p in pts]
        x_mean = sum(xs) / n
        y_mean = sum(ys) / n
        num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
        den = sum((x - x_mean) ** 2 for x in xs)
        return num / den if den else 0.0

    def is_trending_up(self, job_name: str, threshold: float = 1.0) -> bool:
        """Return True if slope exceeds threshold seconds-per-run."""
        s = self.slope(job_name)
        return s is not None and s > threshold

    def clear(self, job_name: str) -> None:
        self._data.pop(job_name, None)
        self._save()
