"""Tests for cronwatch.backoff."""

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from cronwatch.backoff import BackoffStore, BackoffEntry, _fmt


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "backoff.json")


@pytest.fixture
def store(store_file):
    return BackoffStore(store_file, base_s=60, max_s=3600, factor=2.0)


def _past(seconds: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=seconds)


def test_empty_store_has_no_entries(store):
    assert store._data == {}


def test_get_unknown_job_returns_default(store):
    entry = store.get("myjob")
    assert entry.job == "myjob"
    assert entry.attempt == 0
    assert entry.last_alert is None


def test_interval_starts_at_base(store):
    assert store.interval_s("myjob") == 60


def test_interval_doubles_each_attempt(store):
    store.record_alert("myjob")   # attempt -> 1
    assert store.interval_s("myjob") == 120
    store.record_alert("myjob")   # attempt -> 2
    assert store.interval_s("myjob") == 240


def test_interval_capped_at_max(store):
    for _ in range(20):
        store.record_alert("myjob")
    assert store.interval_s("myjob") == 3600


def test_is_ready_with_no_history(store):
    assert store.is_ready("myjob") is True


def test_is_ready_false_within_interval(store, store_file):
    # Manually inject a recent alert
    entry = BackoffEntry("myjob", attempt=0, last_alert=datetime.now(timezone.utc))
    store._data["myjob"] = entry
    store._save = lambda: None  # skip disk
    assert store.is_ready("myjob") is False


def test_is_ready_true_after_interval(store):
    # Inject an old alert (2 minutes ago) with base_s=60
    entry = BackoffEntry("myjob", attempt=0, last_alert=_past(120))
    store._data["myjob"] = entry
    assert store.is_ready("myjob") is True


def test_record_alert_increments_attempt(store):
    store.record_alert("myjob")
    assert store.get("myjob").attempt == 1
    store.record_alert("myjob")
    assert store.get("myjob").attempt == 2


def test_record_alert_persists_to_disk(store, store_file):
    store.record_alert("myjob")
    raw = json.loads(Path(store_file).read_text())
    assert "myjob" in raw
    assert raw["myjob"]["attempt"] == 1


def test_reset_removes_entry(store):
    store.record_alert("myjob")
    store.reset("myjob")
    assert "myjob" not in store._data


def test_reset_unknown_job_is_noop(store):
    store.reset("ghost")  # should not raise


def test_persistence_roundtrip(store, store_file):
    store.record_alert("job_a")
    store.record_alert("job_a")
    store2 = BackoffStore(store_file, base_s=60, max_s=3600, factor=2.0)
    assert store2.get("job_a").attempt == 2
