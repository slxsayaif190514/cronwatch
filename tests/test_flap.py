"""Tests for cronwatch.flap flap-detection store."""

import pytest

from cronwatch.flap import FlapStore


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "flap.json")


@pytest.fixture
def store(store_file):
    return FlapStore(store_file, window=5)


# ------------------------------------------------------------------

def test_empty_store_returns_no_jobs(store):
    assert store.all_jobs() == []


def test_get_outcomes_unknown_job_returns_empty(store):
    assert store.get_outcomes("backup") == []


def test_is_flapping_unknown_job_returns_false(store):
    assert store.is_flapping("backup") is False


def test_record_persists_outcome(store, store_file):
    store.record("backup", True)
    store2 = FlapStore(store_file, window=5)
    assert store2.get_outcomes("backup") == [True]


def test_window_trims_old_outcomes(store):
    for success in [True, False, True, False, True, False]:
        store.record("backup", success)
    outcomes = store.get_outcomes("backup")
    assert len(outcomes) == 5
    assert outcomes == [False, True, False, True, False]


def test_is_flapping_detects_changes(store):
    for success in [True, False, True, False]:
        store.record("backup", success)
    assert store.is_flapping("backup", threshold=2) is True


def test_is_flapping_stable_job_returns_false(store):
    for _ in range(5):
        store.record("backup", True)
    assert store.is_flapping("backup", threshold=2) is False


def test_is_flapping_single_change_below_threshold(store):
    store.record("backup", True)
    store.record("backup", False)
    # only 1 change, threshold=2 → not flapping
    assert store.is_flapping("backup", threshold=2) is False


def test_last_updated_set_after_record(store):
    assert store.last_updated("backup") is None
    store.record("backup", True)
    assert store.last_updated("backup") is not None


def test_reset_clears_job(store):
    store.record("backup", True)
    store.reset("backup")
    assert store.get_outcomes("backup") == []
    assert "backup" not in store.all_jobs()


def test_multiple_jobs_tracked_independently(store):
    store.record("backup", True)
    store.record("cleanup", False)
    assert store.get_outcomes("backup") == [True]
    assert store.get_outcomes("cleanup") == [False]
    assert sorted(store.all_jobs()) == ["backup", "cleanup"]
