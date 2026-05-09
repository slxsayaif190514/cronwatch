"""Tests for cronwatch.burst."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from cronwatch.burst import BurstStore, _fmt


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "burst.json")


@pytest.fixture
def store(store_file):
    return BurstStore(store_file)


def _past(seconds: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=seconds)


def test_empty_store_returns_no_jobs(store):
    assert store.all_jobs() == []


def test_get_count_unknown_job_returns_zero(store):
    assert store.get_count("backup") == 0


def test_is_bursting_unknown_job_returns_false(store):
    assert store.is_bursting("backup", max_runs=5) is False


def test_record_increments_count(store):
    store.record("backup")
    store.record("backup")
    assert store.get_count("backup") == 2


def test_record_persists_to_disk(store, store_file):
    store.record("sync")
    raw = json.loads(open(store_file).read())
    jobs = [e["job"] for e in raw["entries"]]
    assert "sync" in jobs


def test_old_timestamps_pruned_on_record(store_file):
    # Manually inject an old timestamp
    old_ts = _fmt(_past(7200))
    data = {"entries": [{"job": "cleanup", "timestamps": [old_ts]}]}
    with open(store_file, "w") as f:
        json.dump(data, f)
    s = BurstStore(store_file)
    s.record("cleanup", window_seconds=3600)
    # old entry should be pruned; only the new one remains
    assert s.get_count("cleanup", window_seconds=3600) == 1


def test_is_bursting_true_when_over_limit(store):
    for _ in range(6):
        store.record("nightly")
    assert store.is_bursting("nightly", max_runs=5) is True


def test_is_bursting_false_at_limit(store):
    for _ in range(5):
        store.record("nightly")
    assert store.is_bursting("nightly", max_runs=5) is False


def test_reset_clears_job(store):
    store.record("report")
    store.reset("report")
    assert store.get_count("report") == 0
    assert "report" not in store.all_jobs()


def test_all_jobs_sorted(store):
    store.record("zebra")
    store.record("alpha")
    assert store.all_jobs() == ["alpha", "zebra"]
