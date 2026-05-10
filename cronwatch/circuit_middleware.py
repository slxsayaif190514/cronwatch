"""Middleware that records job outcomes into the circuit breaker store."""

from __future__ import annotations

from typing import Callable
from cronwatch.circuit import CircuitStore
from cronwatch.tracker import JobState


class CircuitMiddleware:
    """Wraps a monitor check function to update circuit breaker state."""

    def __init__(self, store: CircuitStore):
        self._store = store

    def wrap(self, fn: Callable) -> Callable:
        def _inner(job_name: str, state: JobState) -> None:
            fn(job_name, state)
            self.record_from_state(job_name, state)
        return _inner

    def record_from_state(self, job_name: str, state: JobState) -> None:
        if state.consecutive_failures and state.consecutive_failures > 0:
            self._store.record_failure(job_name)
        elif state.consecutive_failures == 0:
            self._store.record_success(job_name)

    def is_open(self, job_name: str) -> bool:
        return self._store.is_open(job_name)
