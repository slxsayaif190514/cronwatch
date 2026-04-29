"""Tests for cronwatch.snapshot."""

import json
import os
import time

import pytest

from cronwatch.snapshot import JobSnapshot, Snapshot, SnapshotStore


@pytest.fixture
def snap_file(tmp_path):
    return str(tmp_path / "snapshot.json")


@pytest.fixture
def store(snap_file):
    return SnapshotStore(snap_file)


def _make_job(name="backup", overdue=False, silenced=False, failures=0):
    return JobSnapshot(
        job_name=name,
        last_run="2024-01-01T00:00:00+00:00",
        last_status="success",
        consecutive_failures=failures,
        is_overdue=overdue,
        silenced=silenced,
    )


def test_load_returns_none_when_no_file(store):
    assert store.load() is None


def test_save_creates_file(store, snap_file):
    store.save([_make_job()])
    assert os.path.exists(snap_file)


def test_save_and_load_roundtrip(store):
    jobs = [_make_job("backup"), _make_job("cleanup", overdue=True)]
    store.save(jobs)
    snap = store.load()
    assert snap is not None
    assert len(snap.jobs) == 2
    names = {j["job_name"] for j in snap.jobs}
    assert names == {"backup", "cleanup"}


def test_save_records_captured_at(store):
    store.save([_make_job()])
    snap = store.load()
    assert snap.captured_at is not None
    assert "T" in snap.captured_at


def test_overdue_flag_persisted(store):
    store.save([_make_job("job1", overdue=True)])
    snap = store.load()
    assert snap.jobs[0]["is_overdue"] is True


def test_silenced_flag_persisted(store):
    store.save([_make_job("job1", silenced=True)])
    snap = store.load()
    assert snap.jobs[0]["silenced"] is True


def test_consecutive_failures_persisted(store):
    store.save([_make_job("job1", failures=3)])
    snap = store.load()
    assert snap.jobs[0]["consecutive_failures"] == 3


def test_age_seconds_none_before_first_save(store):
    assert store.age_seconds() is None


def test_age_seconds_small_after_save(store):
    store.save([_make_job()])
    age = store.age_seconds()
    assert age is not None
    assert 0 <= age < 5


def test_empty_jobs_list(store):
    snap = store.save([])
    assert snap.jobs == []
    loaded = store.load()
    assert loaded.jobs == []
