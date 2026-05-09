"""Track and report schedule drift — how far off from expected run times jobs actually fire."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


class DriftSample:
    def __init__(self, expected: datetime, actual: datetime) -> None:
        self.expected = expected
        self.actual = actual
        self.delta_s: float = (actual - expected).total_seconds()

    def to_dict(self) -> dict:
        return {
            "expected": _fmt(self.expected),
            "actual": _fmt(self.actual),
            "delta_s": round(self.delta_s, 3),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DriftSample":
        obj = cls.__new__(cls)
        obj.expected = _parse(d["expected"])
        obj.actual = _parse(d["actual"])
        obj.delta_s = d["delta_s"]
        return obj


class DriftStore:
    def __init__(self, path: str, max_samples: int = 50) -> None:
        self._path = path
        self._max = max_samples
        self._data: Dict[str, List[dict]] = {}
        if os.path.exists(path):
            with open(path) as fh:
                self._data = json.load(fh)

    def _save(self) -> None:
        with open(self._path, "w") as fh:
            json.dump(self._data, fh, indent=2)

    def record(self, job_name: str, expected: datetime, actual: datetime) -> DriftSample:
        sample = DriftSample(expected, actual)
        bucket = self._data.setdefault(job_name, [])
        bucket.append(sample.to_dict())
        if len(bucket) > self._max:
            bucket[:] = bucket[-self._max :]
        self._save()
        return sample

    def get_samples(self, job_name: str) -> List[DriftSample]:
        return [DriftSample.from_dict(d) for d in self._data.get(job_name, [])]

    def avg_drift_s(self, job_name: str) -> Optional[float]:
        samples = self.get_samples(job_name)
        if not samples:
            return None
        return sum(s.delta_s for s in samples) / len(samples)

    def max_drift_s(self, job_name: str) -> Optional[float]:
        samples = self.get_samples(job_name)
        if not samples:
            return None
        return max(abs(s.delta_s) for s in samples)

    def reset(self, job_name: str) -> None:
        self._data.pop(job_name, None)
        self._save()

    def all_jobs(self) -> List[str]:
        return sorted(self._data.keys())
