"""Tests for cronwatch.baseline."""

from __future__ import annotations

import json
import os
import pytest

from cronwatch.baseline import BaselineStore, BaselineStats


@pytest.fixture
def baseline_file(tmp_path):
    return str(tmp_path / "baseline.json")


@pytest.fixture
def store(baseline_file):
    return BaselineStore(baseline_file)


def test_empty_store_returns_no_stats(store):
    assert store.all_stats() == []


def test_get_unknown_job_returns_none(store):
    assert store.get("missing_job") is None


def test_first_update_creates_entry(store):
    stats = store.update("backup", 30.0)
    assert stats.job_name == "backup"
    assert stats.sample_count == 1
    assert stats.avg_duration_s == 30.0
    assert stats.stddev_s == 0.0


def test_second_update_computes_avg(store):
    store.update("backup", 20.0)
    stats = store.update("backup", 40.0)
    assert stats.sample_count == 2
    assert abs(stats.avg_duration_s - 30.0) < 0.01


def test_stddev_increases_with_variance(store):
    store.update("job", 10.0)
    store.update("job", 10.0)
    stats_low = store.update("job", 10.0)

    store2 = BaselineStore.__new__(BaselineStore)
    store2._path = store._path + "2"
    store2._data = {}
    store2.update("job", 10.0)
    store2.update("job", 50.0)
    stats_high = store2.update("job", 100.0)

    assert stats_high.stddev_s > stats_low.stddev_s


def test_update_persists_to_disk(baseline_file, store):
    store.update("daily_report", 60.0)
    store2 = BaselineStore(baseline_file)
    s = store2.get("daily_report")
    assert s is not None
    assert s.avg_duration_s == 60.0


def test_reset_removes_entry(store):
    store.update("cleanup", 5.0)
    removed = store.reset("cleanup")
    assert removed is True
    assert store.get("cleanup") is None


def test_reset_nonexistent_returns_false(store):
    assert store.reset("ghost_job") is False


def test_upper_bound_default_sigma():
    s = BaselineStats(
        job_name="j",
        sample_count=10,
        avg_duration_s=100.0,
        stddev_s=10.0,
        updated_at="2024-01-01T00:00:00+00:00",
    )
    assert s.upper_bound() == pytest.approx(120.0)


def test_upper_bound_custom_sigma():
    s = BaselineStats(
        job_name="j",
        sample_count=10,
        avg_duration_s=50.0,
        stddev_s=5.0,
        updated_at="2024-01-01T00:00:00+00:00",
    )
    assert s.upper_bound(sigma=3.0) == pytest.approx(65.0)


def test_all_stats_returns_all_jobs(store):
    store.update("job_a", 10.0)
    store.update("job_b", 20.0)
    names = {s.job_name for s in store.all_stats()}
    assert names == {"job_a", "job_b"}
