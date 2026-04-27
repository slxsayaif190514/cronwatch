"""Periodic digest builder: aggregates recent alerts into a single summary."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

_DT_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime(_DT_FMT)


def _parse(s: str) -> datetime:
    return datetime.strptime(s, _DT_FMT).replace(tzinfo=timezone.utc)


class DigestStore:
    """Persists pending alert events for later digest dispatch."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._events: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path) as fh:
                    self._events = json.load(fh)
            except (json.JSONDecodeError, OSError):
                self._events = []
        else:
            self._events = []

    def _save(self) -> None:
        with open(self.path, "w") as fh:
            json.dump(self._events, fh, indent=2)

    def add_event(self, job_name: str, kind: str, message: str) -> None:
        """Record a new alert event."""
        self._events.append(
            {"job": job_name, "kind": kind, "message": message, "at": _fmt(_now())}
        )
        self._save()

    def pending(self) -> List[Dict[str, Any]]:
        """Return all pending events."""
        return list(self._events)

    def clear(self) -> None:
        """Remove all pending events after digest has been sent."""
        self._events = []
        self._save()


def build_digest(events: List[Dict[str, Any]]) -> str:
    """Render a human-readable digest from a list of events."""
    if not events:
        return "No alerts to report."
    lines = [f"cronwatch digest — {len(events)} alert(s)\n"]
    for ev in events:
        lines.append(f"  [{ev['at']}] {ev['job']} — {ev['kind']}: {ev['message']}")
    return "\n".join(lines)
