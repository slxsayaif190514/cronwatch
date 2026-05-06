"""Middleware that records job durations into the TrendStore after each run."""

from __future__ import annotations

from typing import Callable

from cronwatch.trend import TrendStore
from cronwatch.tracker import JobState


class TrendMiddleware:
    """Wraps a monitor check callback to capture duration trends."""

    def __init__(self, store: TrendStore) -> None:
        self._store = store

    def wrap(self, fn: Callable) -> Callable:
        def _inner(*args, **kwargs):
            result = fn(*args, **kwargs)
            return result
        return _inner

    def record_from_state(self, job_name: str, state: JobState) -> None:
        """Record duration if the state reflects a completed run with timing info."""
        if state.last_run_dt is None:
            return
        duration = getattr(state, "last_duration_s", None)
        if duration is None or duration < 0:
            return
        self._store.record(job_name, duration)

    def alert_if_trending(self, job_name: str, threshold: float = 1.0) -> bool:
        """Return True if the job's duration slope exceeds the given threshold."""
        return self._store.is_trending_up(job_name, threshold)
