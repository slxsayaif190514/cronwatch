"""Tests for cronwatch.heartbeat."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from cronwatch.heartbeat import HeartbeatStore


def _utc(**kwargs) -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0) + timedelta(**kwargs)


@pytest.fixture()
def store_file(tmp_path):
    return str(tmp_path / "heartbeats.json")


@pytest.fixture()
def store(store_file):
    return HeartbeatStore(store_file)


def test_empty_store_has_no_jobs(store):
    assert store.all_jobs() == []


def test_last_ping_unknown_job_returns_none(store):
    assert store.last_ping("backup") is None


def test_ping_persists_to_disk(store_file):
    s = HeartbeatStore(store_file)
    ts = _utc()
    s.ping("backup", at=ts)

    s2 = HeartbeatStore(store_file)
    assert s2.last_ping("backup") == ts


def test_ping_returns_recorded_timestamp(store):
    ts = _utc()
    result = store.ping("nightly", at=ts)
    assert result == ts


def test_ping_updates_existing_entry(store):
    old = _utc(seconds=-120)
    new = _utc()
    store.ping("cleanup", at=old)
    store.ping("cleanup", at=new)
    assert store.last_ping("cleanup") == new


def test_is_stale_returns_true_when_no_ping(store):
    assert store.is_stale("missing", max_age_seconds=60) is True


def test_is_stale_returns_false_when_recent(store):
    store.ping("recent", at=_utc(seconds=-10))
    assert store.is_stale("recent", max_age_seconds=60) is False


def test_is_stale_returns_true_when_old(store):
    store.ping("old", at=_utc(seconds=-200))
    assert store.is_stale("old", max_age_seconds=60) is True


def test_all_jobs_sorted(store):
    store.ping("zebra")
    store.ping("alpha")
    store.ping("middle")
    assert store.all_jobs() == ["alpha", "middle", "zebra"]


def test_remove_existing_job(store):
    store.ping("temp")
    assert store.remove("temp") is True
    assert store.last_ping("temp") is None


def test_remove_unknown_job_returns_false(store):
    assert store.remove("ghost") is False
