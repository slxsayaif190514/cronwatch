"""Middleware that records metrics automatically during monitor run_checks."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Optional

from cronwatch.metrics import MetricsStore


class MetricsMiddleware:
    """Wraps a job execution callable and records duration + outcome."""

    def __init__(self, store: MetricsStore) -> None:
        self._store = store

    def wrap(self, job_name: str, fn: Callable[[], bool]) -> Callable[[], bool]:
        """Return a wrapped callable that records metrics around fn()."""
        def _inner() -> bool:
            start = time.monotonic()
            try:
                success = fn()
            except Exception:
                success = False
            finally:
                duration = time.monotonic() - start
            self._store.record(job_name, success=success, duration_s=duration)
            return success
        return _inner

    def record_from_state(self, job_name: str, success: bool, duration_s: float) -> None:
        """Directly record a known outcome without wrapping a callable."""
        self._store.record(job_name, success=success, duration_s=duration_s)


def make_middleware(metrics_path: Optional[Path] = None) -> MetricsMiddleware:
    path = metrics_path or Path("metrics.json")
    return MetricsMiddleware(MetricsStore(path))
