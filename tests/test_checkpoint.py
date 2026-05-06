"""Tests for cronwatch.checkpoint."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta

import pytest

from cronwatch.checkpoint import CheckpointStore


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "checkpoints.json")


@pytest.fixture
def store(store_file):
    return CheckpointStore(store_file)


def _utc(**kw):
    return datetime.now(timezone.utc).replace(microsecond=0) - timedelta(**kw)


def test_empty_store_returns_no_entries(store):
    assert store.all() == {}


def test_get_unknown_job_returns_none(store):
    assert store.get("missing") is None


def test_set_persists_to_disk(store, store_file):
    store.set("backup")
    raw = json.loads(open(store_file).read())
    assert "backup" in raw


def test_set_with_explicit_dt(store):
    dt = _utc(hours=1)
    stored = store.set("myjob", dt)
    assert stored == dt
    retrieved = store.get("myjob")
    # Round-trip through seconds-precision format
    assert retrieved == dt.replace(microsecond=0)


def test_set_defaults_to_now(store):
    before = datetime.now(timezone.utc).replace(microsecond=0)
    store.set("job1")
    after = datetime.now(timezone.utc)
    cp = store.get("job1")
    assert cp is not None
    assert before <= cp <= after


def test_remove_existing_returns_true(store):
    store.set("job2")
    assert store.remove("job2") is True
    assert store.get("job2") is None


def test_remove_missing_returns_false(store):
    assert store.remove("ghost") is False


def test_age_seconds_returns_none_when_no_checkpoint(store):
    assert store.age_seconds("nope") is None


def test_age_seconds_is_positive(store):
    dt = _utc(seconds=30)
    store.set("aged", dt)
    age = store.age_seconds("aged")
    assert age is not None
    assert 25 <= age <= 60  # generous window for test timing


def test_all_returns_all_jobs(store):
    store.set("a")
    store.set("b")
    result = store.all()
    assert set(result.keys()) == {"a", "b"}


def test_store_reloads_from_disk(store_file):
    s1 = CheckpointStore(store_file)
    s1.set("persistent")
    s2 = CheckpointStore(store_file)
    assert s2.get("persistent") is not None
