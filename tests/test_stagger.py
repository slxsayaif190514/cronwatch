"""Tests for cronwatch.stagger."""

import json
import os
import pytest

from cronwatch.stagger import StaggerEntry, StaggerStore


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "stagger.json")


@pytest.fixture
def store(store_file):
    return StaggerStore(store_file)


def test_empty_store_returns_no_entries(store):
    assert store.all() == []


def test_get_unknown_job_returns_none(store):
    assert store.get("backup") is None


def test_set_persists_to_disk(store, store_file):
    store.set("backup", 30, reason="avoid overlap")
    assert os.path.exists(store_file)
    with open(store_file) as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["job_name"] == "backup"
    assert data[0]["offset_seconds"] == 30
    assert data[0]["reason"] == "avoid overlap"


def test_get_returns_entry_after_set(store):
    store.set("cleanup", 60)
    entry = store.get("cleanup")
    assert entry is not None
    assert entry.offset_seconds == 60
    assert entry.job_name == "cleanup"


def test_set_updates_existing_entry(store):
    store.set("cleanup", 60)
    store.set("cleanup", 90, reason="updated")
    entry = store.get("cleanup")
    assert entry.offset_seconds == 90
    assert entry.reason == "updated"
    assert len(store.all()) == 1


def test_remove_existing_entry(store):
    store.set("job_a", 15)
    result = store.remove("job_a")
    assert result is True
    assert store.get("job_a") is None


def test_remove_nonexistent_returns_false(store):
    assert store.remove("ghost") is False


def test_all_returns_sorted_by_job_name(store):
    store.set("zebra", 10)
    store.set("alpha", 20)
    store.set("middle", 5)
    names = [e.job_name for e in store.all()]
    assert names == ["alpha", "middle", "zebra"]


def test_store_reloads_from_disk(store_file):
    s1 = StaggerStore(store_file)
    s1.set("persist_job", 45, reason="test reload")
    s2 = StaggerStore(store_file)
    entry = s2.get("persist_job")
    assert entry is not None
    assert entry.offset_seconds == 45
    assert entry.reason == "test reload"


def test_entry_to_dict_roundtrip():
    from datetime import datetime, timezone
    dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    e = StaggerEntry("myjob", 120, "reason", dt)
    d = e.to_dict()
    e2 = StaggerEntry.from_dict(d)
    assert e2.job_name == "myjob"
    assert e2.offset_seconds == 120
    assert e2.reason == "reason"
    assert e2.updated_at == dt
