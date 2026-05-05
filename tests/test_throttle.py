"""Tests for cronwatch.throttle."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from cronwatch.throttle import ThrottleStore, _fmt


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "throttle.json")


@pytest.fixture
def store(store_file):
    return ThrottleStore(path=store_file, window_seconds=3600, max_burst=3)


def _past(seconds: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=seconds)


def test_empty_store_not_throttled(store):
    assert store.is_throttled("backup") is False


def test_record_alert_increments_count(store):
    store.record_alert("backup")
    store.record_alert("backup")
    entry = store.get_entry("backup")
    assert entry.count == 2


def test_throttled_after_burst_exceeded(store):
    for _ in range(3):
        store.record_alert("backup")
    assert store.is_throttled("backup") is True


def test_not_throttled_below_burst(store):
    for _ in range(2):
        store.record_alert("backup")
    assert store.is_throttled("backup") is False


def test_window_reset_clears_count(store_file):
    store = ThrottleStore(path=store_file, window_seconds=60, max_burst=2)
    for _ in range(2):
        store.record_alert("nightly")
    assert store.is_throttled("nightly") is True

    # Simulate window expiry by backdating window_start
    entry = store.get_entry("nightly")
    entry.window_start = _past(120)

    # Re-check — window expired, count should reset
    assert store.is_throttled("nightly") is False


def test_reset_removes_entry(store):
    store.record_alert("cleanup")
    store.reset("cleanup")
    assert store.get_entry("cleanup") is None


def test_reset_all_clears_all_entries(store):
    store.record_alert("job-a")
    store.record_alert("job-b")
    for job in list(store._data.keys()):
        store.reset(job)
    assert store._data == {}


def test_persists_to_disk(store_file):
    s = ThrottleStore(path=store_file, window_seconds=3600, max_burst=5)
    s.record_alert("deploy")
    s.record_alert("deploy")

    s2 = ThrottleStore(path=store_file, window_seconds=3600, max_burst=5)
    assert s2.get_entry("deploy").count == 2


def test_last_alert_updated_on_record(store):
    store.record_alert("sync")
    entry = store.get_entry("sync")
    assert entry.last_alert is not None
