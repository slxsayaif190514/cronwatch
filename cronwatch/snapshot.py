"""Point-in-time snapshot of all job states for reporting and diagnostics."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _parse(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    return datetime.fromisoformat(s)


@dataclass
class JobSnapshot:
    job_name: str
    last_run: Optional[str]
    last_status: Optional[str]  # "success" | "failure" | None
    consecutive_failures: int
    is_overdue: bool
    silenced: bool


@dataclass
class Snapshot:
    captured_at: str
    jobs: List[Dict]

    def to_dict(self) -> Dict:
        return {
            "captured_at": self.captured_at,
            "jobs": self.jobs,
        }


class SnapshotStore:
    def __init__(self, path: str) -> None:
        self._path = path

    def save(self, jobs: List[JobSnapshot]) -> Snapshot:
        snap = Snapshot(
            captured_at=_fmt(_utcnow()),
            jobs=[asdict(j) for j in jobs],
        )
        with open(self._path, "w") as fh:
            json.dump(snap.to_dict(), fh, indent=2)
        return snap

    def load(self) -> Optional[Snapshot]:
        """Load the snapshot from disk, returning None if it doesn't exist.

        Raises ``ValueError`` if the file exists but contains invalid JSON or
        is missing the required ``captured_at`` field.
        """
        if not os.path.exists(self._path):
            return None
        with open(self._path) as fh:
            try:
                data = json.load(fh)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Snapshot file {self._path!r} contains invalid JSON"
                ) from exc
        if "captured_at" not in data:
            raise ValueError(
                f"Snapshot file {self._path!r} is missing 'captured_at' field"
            )
        return Snapshot(
            captured_at=data["captured_at"],
            jobs=data.get("jobs", []),
        )

    def age_seconds(self) -> Optional[float]:
        """Return how many seconds ago the snapshot was captured, or None."""
        snap = self.load()
        if snap is None:
            return None
        captured = _parse(snap.captured_at)
        if captured is None:
            return None
        return (_utcnow() - captured).total_seconds()
