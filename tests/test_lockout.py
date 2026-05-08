"""Tests for cronwatch.lockout."""

import pytest
from datetime import timezone

from cronwatch.lockout import LockoutStore


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "lockouts.json")


@pytest.fixture
def store(store_file):
    return LockoutStore(store_file)


def test_empty_store_has_no_entries(store):
    assert store.all() == []


def test_is_locked_unknown_job_returns_false(store):
    assert store.is_locked("backup") is False


def test_get_unknown_job_returns_none(store):
    assert store.get("backup") is None


def test_lock_persists_to_disk(store_file):
    s = LockoutStore(store_file)
    s.lock("backup", reason="maintenance", locked_by="alice")

    s2 = LockoutStore(store_file)
    assert s2.is_locked("backup")
    entry = s2.get("backup")
    assert entry.reason == "maintenance"
    assert entry.locked_by == "alice"
    assert entry.locked_at.tzinfo == timezone.utc


def test_lock_returns_entry(store):
    entry = store.lock("cleanup", reason="testing")
    assert entry.job_name == "cleanup"
    assert entry.reason == "testing"
    assert entry.locked_by == "admin"


def test_is_locked_after_lock(store):
    store.lock("daily_report", reason="paused")
    assert store.is_locked("daily_report") is True


def test_unlock_removes_entry(store):
    store.lock("sync", reason="deploy")
    result = store.unlock("sync")
    assert result is True
    assert store.is_locked("sync") is False


def test_unlock_unknown_job_returns_false(store):
    result = store.unlock("nonexistent")
    assert result is False


def test_unlock_persists_to_disk(store_file):
    s = LockoutStore(store_file)
    s.lock("etl", reason="hold")
    s.unlock("etl")

    s2 = LockoutStore(store_file)
    assert not s2.is_locked("etl")


def test_all_returns_sorted_by_job_name(store):
    store.lock("zebra_job", reason="z")
    store.lock("alpha_job", reason="a")
    store.lock("middle_job", reason="m")
    names = [e.job_name for e in store.all()]
    assert names == ["alpha_job", "middle_job", "zebra_job"]


def test_lock_overwrites_existing(store):
    store.lock("backup", reason="first", locked_by="alice")
    store.lock("backup", reason="second", locked_by="bob")
    entry = store.get("backup")
    assert entry.reason == "second"
    assert entry.locked_by == "bob"
    assert len(store.all()) == 1
