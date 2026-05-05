"""Tests for cronwatch.metrics."""

import json
from pathlib import Path

import pytest

from cronwatch.metrics import JobMetrics, MetricsStore


@pytest.fixture
def metrics_file(tmp_path):
    return tmp_path / "metrics.json"


@pytest.fixture
def store(metrics_file):
    return MetricsStore(metrics_file)


def test_get_unknown_job_returns_empty(store):
    m = store.get("backup")
    assert m.job_name == "backup"
    assert m.total_runs == 0
    assert m.success_runs == 0
    assert m.failure_runs == 0


def test_record_success_increments(store):
    m = store.record("backup", success=True, duration_s=1.5)
    assert m.total_runs == 1
    assert m.success_runs == 1
    assert m.failure_runs == 0


def test_record_failure_increments(store):
    m = store.record("backup", success=False, duration_s=0.3)
    assert m.failure_runs == 1
    assert m.success_runs == 0


def test_duration_stats(store):
    store.record("job", success=True, duration_s=2.0)
    store.record("job", success=True, duration_s=4.0)
    m = store.get("job")
    assert m.min_duration_s == pytest.approx(2.0)
    assert m.max_duration_s == pytest.approx(4.0)
    assert m.avg_duration_s == pytest.approx(3.0)


def test_persists_to_disk(store, metrics_file):
    store.record("sync", success=True, duration_s=1.0)
    store2 = MetricsStore(metrics_file)
    m = store2.get("sync")
    assert m.total_runs == 1


def test_all_metrics_returns_all(store):
    store.record("a", success=True, duration_s=1.0)
    store.record("b", success=False, duration_s=2.0)
    names = {m.job_name for m in store.all_metrics()}
    assert names == {"a", "b"}


def test_reset_removes_job(store):
    store.record("cleanup", success=True, duration_s=0.5)
    store.reset("cleanup")
    m = store.get("cleanup")
    assert m.total_runs == 0


def test_avg_duration_none_when_no_runs():
    m = JobMetrics(job_name="x")
    assert m.avg_duration_s is None


def test_to_dict_round_trips():
    m = JobMetrics(job_name="j", total_runs=3, success_runs=2, failure_runs=1,
                   total_duration_s=6.0, min_duration_s=1.5, max_duration_s=3.0)
    m2 = JobMetrics.from_dict(m.to_dict())
    assert m2.job_name == "j"
    assert m2.total_runs == 3
    assert m2.avg_duration_s == pytest.approx(2.0)
