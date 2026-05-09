"""Tests for cronwatch.drift."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

import pytest

from cronwatch.drift import DriftStore, DriftSample


def _utc(**kwargs) -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(**kwargs)


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "drift.json")


@pytest.fixture
def store(store_file):
    return DriftStore(store_file)


def test_empty_store_returns_no_jobs(store):
    assert store.all_jobs() == []


def test_get_samples_unknown_job_returns_empty(store):
    assert store.get_samples("backup") == []


def test_avg_drift_unknown_job_returns_none(store):
    assert store.avg_drift_s("backup") is None


def test_max_drift_unknown_job_returns_none(store):
    assert store.max_drift_s("backup") is None


def test_record_persists_sample(store, store_file):
    expected = _utc()
    actual = _utc(seconds=30)
    store.record("backup", expected, actual)

    store2 = DriftStore(store_file)
    samples = store2.get_samples("backup")
    assert len(samples) == 1
    assert samples[0].delta_s == pytest.approx(30.0)


def test_record_multiple_samples(store):
    for offset in [10, 20, 30]:
        store.record("sync", _utc(), _utc(seconds=offset))
    samples = store.get_samples("sync")
    assert len(samples) == 3


def test_avg_drift_computed_correctly(store):
    store.record("sync", _utc(), _utc(seconds=10))
    store.record("sync", _utc(), _utc(seconds=30))
    assert store.avg_drift_s("sync") == pytest.approx(20.0)


def test_max_drift_uses_absolute_value(store):
    store.record("sync", _utc(), _utc(seconds=-5))   # early
    store.record("sync", _utc(), _utc(seconds=15))
    assert store.max_drift_s("sync") == pytest.approx(15.0)


def test_max_samples_cap(store_file):
    s = DriftStore(store_file, max_samples=5)
    for i in range(8):
        s.record("job", _utc(), _utc(seconds=i))
    assert len(s.get_samples("job")) == 5


def test_reset_clears_samples(store):
    store.record("job", _utc(), _utc(seconds=5))
    store.reset("job")
    assert store.get_samples("job") == []
    assert "job" not in store.all_jobs()


def test_all_jobs_sorted(store):
    store.record("z_job", _utc(), _utc(seconds=1))
    store.record("a_job", _utc(), _utc(seconds=2))
    assert store.all_jobs() == ["a_job", "z_job"]
