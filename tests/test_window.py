"""Tests for cronwatch.window"""

import pytest
from datetime import datetime, timezone, timedelta
from cronwatch.window import WindowStore, WindowEntry


def _utc(year=2024, month=1, day=1, hour=0, minute=0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "windows.json")


@pytest.fixture
def store(store_file):
    return WindowStore(store_file)


def test_empty_store_has_no_windows(store):
    assert store.get_windows("backup") == []


def test_add_window_persists(store, store_file):
    start = _utc(hour=2)
    end = _utc(hour=3)
    store.add_window("backup", start, end)
    reloaded = WindowStore(store_file)
    windows = reloaded.get_windows("backup")
    assert len(windows) == 1
    assert windows[0].job_name == "backup"
    assert windows[0].ran is False


def test_mark_ran_within_window(store):
    start = _utc(hour=2)
    end = _utc(hour=4)
    store.add_window("backup", start, end)
    result = store.mark_ran("backup", at=_utc(hour=3))
    assert result is True
    assert store.get_windows("backup")[0].ran is True


def test_mark_ran_outside_window_returns_false(store):
    start = _utc(hour=2)
    end = _utc(hour=3)
    store.add_window("backup", start, end)
    result = store.mark_ran("backup", at=_utc(hour=5))
    assert result is False


def test_mark_ran_already_ran_returns_false(store):
    start = _utc(hour=2)
    end = _utc(hour=4)
    store.add_window("backup", start, end)
    store.mark_ran("backup", at=_utc(hour=3))
    result = store.mark_ran("backup", at=_utc(hour=3, minute=30))
    assert result is False


def test_missed_windows_returns_closed_unran(store):
    store.add_window("sync", _utc(hour=1), _utc(hour=2))
    store.add_window("sync", _utc(hour=3), _utc(hour=4))
    store.mark_ran("sync", at=_utc(hour=1, minute=30))
    missed = store.missed_windows("sync", before=_utc(hour=5))
    assert len(missed) == 1
    assert missed[0].window_start == _utc(hour=3)


def test_missed_windows_excludes_open_window(store):
    now = _utc(hour=3)
    store.add_window("sync", _utc(hour=2), _utc(hour=5))
    missed = store.missed_windows("sync", before=now)
    assert missed == []


def test_clear_removes_all_windows_for_job(store):
    store.add_window("job_a", _utc(hour=1), _utc(hour=2))
    store.add_window("job_a", _utc(hour=3), _utc(hour=4))
    store.add_window("job_b", _utc(hour=1), _utc(hour=2))
    removed = store.clear("job_a")
    assert removed == 2
    assert store.get_windows("job_a") == []
    assert len(store.get_windows("job_b")) == 1


def test_multiple_jobs_isolated(store):
    store.add_window("alpha", _utc(hour=1), _utc(hour=2))
    store.add_window("beta", _utc(hour=1), _utc(hour=2))
    store.mark_ran("alpha", at=_utc(hour=1, minute=30))
    assert store.get_windows("alpha")[0].ran is True
    assert store.get_windows("beta")[0].ran is False
