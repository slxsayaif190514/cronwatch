"""Tests for cronwatch.trend."""

from __future__ import annotations

import os
import pytest

from cronwatch.trend import TrendStore, TrendPoint


@pytest.fixture
def trend_file(tmp_path):
    return str(tmp_path / "trend.json")


@pytest.fixture
def store(trend_file):
    return TrendStore(trend_file, window=5)


def test_empty_store_returns_no_points(store):
    assert store.get_points("job_a") == []


def test_slope_returns_none_for_empty(store):
    assert store.slope("job_a") is None


def test_slope_returns_none_for_single_point(store):
    store.record("job_a", 10.0)
    assert store.slope("job_a") is None


def test_record_persists_to_disk(store, trend_file):
    store.record("job_a", 5.0)
    store2 = TrendStore(trend_file)
    pts = store2.get_points("job_a")
    assert len(pts) == 1
    assert pts[0].duration_s == 5.0


def test_window_caps_stored_points(trend_file):
    s = TrendStore(trend_file, window=3)
    for i in range(6):
        s.record("job_a", float(i))
    assert len(s.get_points("job_a")) == 3


def test_slope_flat_series_is_zero(store):
    for _ in range(4):
        store.record("job_a", 10.0)
    s = store.slope("job_a")
    assert s is not None
    assert abs(s) < 1e-9


def test_slope_increasing_series_is_positive(store):
    for i in range(5):
        store.record("job_a", float(i * 10))
    s = store.slope("job_a")
    assert s is not None and s > 0


def test_is_trending_up_true_when_slope_exceeds_threshold(store):
    for i in range(5):
        store.record("job_a", float(i * 20))
    assert store.is_trending_up("job_a", threshold=1.0) is True


def test_is_trending_up_false_for_flat(store):
    for _ in range(5):
        store.record("job_a", 5.0)
    assert store.is_trending_up("job_a", threshold=1.0) is False


def test_clear_removes_job_data(store):
    store.record("job_a", 10.0)
    store.clear("job_a")
    assert store.get_points("job_a") == []


def test_multiple_jobs_independent(store):
    store.record("job_a", 1.0)
    store.record("job_b", 99.0)
    assert len(store.get_points("job_a")) == 1
    assert len(store.get_points("job_b")) == 1
