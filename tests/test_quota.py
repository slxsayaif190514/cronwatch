"""Tests for cronwatch.quota."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.quota import QuotaStore


UTC = timezone.utc


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    return tmp_path / "quota.json"


@pytest.fixture()
def store(store_file: Path) -> QuotaStore:
    return QuotaStore(str(store_file), max_alerts=3, window_hours=1)


def _past(hours: float) -> datetime:
    return datetime.now(UTC) - timedelta(hours=hours)


def test_empty_store_not_exceeded(store: QuotaStore) -> None:
    assert store.is_quota_exceeded("backup") is False


def test_get_count_unknown_job_returns_zero(store: QuotaStore) -> None:
    assert store.get_count("nightly") == 0


def test_record_alert_increments_count(store: QuotaStore) -> None:
    count = store.record_alert("backup")
    assert count == 1
    assert store.get_count("backup") == 1


def test_quota_exceeded_after_max_alerts(store: QuotaStore) -> None:
    for _ in range(3):
        store.record_alert("backup")
    assert store.is_quota_exceeded("backup") is True


def test_quota_not_exceeded_below_max(store: QuotaStore) -> None:
    for _ in range(2):
        store.record_alert("backup")
    assert store.is_quota_exceeded("backup") is False


def test_reset_clears_count(store: QuotaStore) -> None:
    store.record_alert("backup")
    store.record_alert("backup")
    store.reset("backup")
    assert store.get_count("backup") == 0
    assert store.is_quota_exceeded("backup") is False


def test_window_expiry_resets_count(store_file: Path) -> None:
    s = QuotaStore(str(store_file), max_alerts=3, window_hours=1)
    s.record_alert("backup")
    s.record_alert("backup")
    # manually backdate the window_start
    raw = json.loads(store_file.read_text())
    raw["backup"]["window_start"] = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    store_file.write_text(json.dumps(raw))
    s2 = QuotaStore(str(store_file), max_alerts=3, window_hours=1)
    assert s2.get_count("backup") == 0
    assert s2.is_quota_exceeded("backup") is False


def test_all_jobs_returns_sorted_active(store: QuotaStore) -> None:
    store.record_alert("zebra")
    store.record_alert("alpha")
    assert store.all_jobs() == ["alpha", "zebra"]


def test_persists_to_disk(store_file: Path) -> None:
    s1 = QuotaStore(str(store_file), max_alerts=5, window_hours=2)
    s1.record_alert("nightly")
    s2 = QuotaStore(str(store_file), max_alerts=5, window_hours=2)
    assert s2.get_count("nightly") == 1
