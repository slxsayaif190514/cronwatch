"""Tests for cronwatch.ratelimit."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from cronwatch.ratelimit import RateLimitStore, _fmt


@pytest.fixture()
def store_file(tmp_path):
    return str(tmp_path / "ratelimit.json")


@pytest.fixture()
def store(store_file):
    return RateLimitStore(store_file)


def _past(seconds: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    return _fmt(dt)


def test_empty_store_not_rate_limited(store):
    assert store.is_rate_limited("job_a", max_alerts=3, window_seconds=300) is False


def test_record_alert_increments_count(store):
    store.record_alert("job_a")
    store.record_alert("job_a")
    assert store.alert_count("job_a", window_seconds=300) == 2


def test_is_rate_limited_at_threshold(store):
    for _ in range(3):
        store.record_alert("job_a")
    assert store.is_rate_limited("job_a", max_alerts=3, window_seconds=300) is True


def test_is_not_rate_limited_below_threshold(store):
    for _ in range(2):
        store.record_alert("job_a")
    assert store.is_rate_limited("job_a", max_alerts=3, window_seconds=300) is False


def test_prune_removes_old_timestamps(store_file):
    # Inject one old and one recent timestamp directly
    data = {"job_b": [_past(600), _past(10)]}
    with open(store_file, "w") as f:
        json.dump(data, f)
    s = RateLimitStore(store_file)
    assert s.alert_count("job_b", window_seconds=300) == 1


def test_prune_removes_all_old_timestamps(store_file):
    data = {"job_c": [_past(400), _past(500)]}
    with open(store_file, "w") as f:
        json.dump(data, f)
    s = RateLimitStore(store_file)
    assert s.alert_count("job_c", window_seconds=300) == 0


def test_reset_clears_job(store):
    store.record_alert("job_a")
    store.reset("job_a")
    assert store.alert_count("job_a", window_seconds=300) == 0


def test_reset_unknown_job_is_noop(store):
    store.reset("nonexistent")  # should not raise


def test_persists_to_disk(store_file):
    s1 = RateLimitStore(store_file)
    s1.record_alert("job_x")
    s2 = RateLimitStore(store_file)
    assert s2.alert_count("job_x", window_seconds=300) == 1


def test_separate_jobs_are_independent(store):
    store.record_alert("job_a")
    store.record_alert("job_a")
    store.record_alert("job_a")
    assert store.is_rate_limited("job_b", max_alerts=3, window_seconds=300) is False
