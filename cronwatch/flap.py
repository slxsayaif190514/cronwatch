"""Flap detection: track rapid state changes (success/failure) for a job."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

_DT_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime(_DT_FMT)


def _parse(s: str) -> datetime:
    return datetime.strptime(s, _DT_FMT).replace(tzinfo=timezone.utc)


class FlapStore:
    """Persist recent outcome history per job and detect flapping."""

    def __init__(self, path: str, window: int = 5) -> None:
        self._path = path
        self._window = window  # number of recent outcomes to keep
        self._data: dict = self._load()

    # ------------------------------------------------------------------
    def _load(self) -> dict:
        if os.path.exists(self._path):
            with open(self._path) as f:
                return json.load(f)
        return {}

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    # ------------------------------------------------------------------
    def record(self, job: str, success: bool) -> None:
        """Append an outcome (True=success, False=failure) for *job*."""
        entry = self._data.setdefault(job, {"outcomes": [], "updated": ""})
        outcomes: List[bool] = entry["outcomes"]
        outcomes.append(success)
        if len(outcomes) > self._window:
            outcomes[:] = outcomes[-self._window :]
        entry["updated"] = _fmt(_utcnow())
        self._save()

    def is_flapping(self, job: str, threshold: int = 2) -> bool:
        """Return True if job has at least *threshold* state changes in window."""
        outcomes = self._data.get(job, {}).get("outcomes", [])
        if len(outcomes) < 2:
            return False
        changes = sum(
            1 for a, b in zip(outcomes, outcomes[1:]) if a != b
        )
        return changes >= threshold

    def get_outcomes(self, job: str) -> List[bool]:
        return list(self._data.get(job, {}).get("outcomes", []))

    def last_updated(self, job: str) -> Optional[datetime]:
        raw = self._data.get(job, {}).get("updated", "")
        return _parse(raw) if raw else None

    def reset(self, job: str) -> None:
        if job in self._data:
            del self._data[job]
            self._save()

    def all_jobs(self) -> List[str]:
        return sorted(self._data.keys())
