"""Tests for cronwatch.circuit."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from cronwatch.circuit import CircuitStore, CircuitEntry, _fmt


@pytest.fixture
def store_file(tmp_path: Path) -> Path:
    return tmp_path / "circuit.json"


@pytest.fixture
def store(store_file: Path) -> CircuitStore:
    return CircuitStore(str(store_file), threshold=3, reset_after_s=600)


def test_empty_store_has_no_entries(store: CircuitStore):
    assert store.get("job_a").failures == 0
    assert store.get("job_a").opened_at is None


def test_is_open_unknown_job_returns_false(store: CircuitStore):
    assert store.is_open("job_a") is False


def test_record_failure_increments(store: CircuitStore):
    store.record_failure("job_a")
    store.record_failure("job_a")
    assert store.get("job_a").failures == 2


def test_circuit_opens_at_threshold(store: CircuitStore):
    for _ in range(3):
        store.record_failure("job_a")
    assert store.is_open("job_a") is True
    assert store.get("job_a").opened_at is not None


def test_circuit_stays_closed_below_threshold(store: CircuitStore):
    store.record_failure("job_a")
    store.record_failure("job_a")
    assert store.is_open("job_a") is False


def test_record_success_resets_circuit(store: CircuitStore):
    for _ in range(3):
        store.record_failure("job_a")
    store.record_success("job_a")
    assert store.get("job_a").failures == 0
    assert store.is_open("job_a") is False


def test_circuit_half_open_after_reset_window(store_file: Path):
    store = CircuitStore(str(store_file), threshold=1, reset_after_s=0)
    store.record_failure("job_a")
    # reset_after_s=0 means it's immediately eligible for half-open
    assert store.is_open("job_a") is False
    assert store.get("job_a").half_open is True


def test_persists_across_reload(store_file: Path):
    s1 = CircuitStore(str(store_file), threshold=3, reset_after_s=600)
    s1.record_failure("job_b")
    s1.record_failure("job_b")
    s2 = CircuitStore(str(store_file), threshold=3, reset_after_s=600)
    assert s2.get("job_b").failures == 2


def test_reset_removes_entry(store: CircuitStore):
    store.record_failure("job_c")
    store.reset("job_c")
    assert store.get("job_c").failures == 0


def test_multiple_jobs_independent(store: CircuitStore):
    for _ in range(3):
        store.record_failure("job_x")
    store.record_failure("job_y")
    assert store.is_open("job_x") is True
    assert store.is_open("job_y") is False
