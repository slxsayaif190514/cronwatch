"""Tests for cronwatch.cooldown."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.cooldown import CooldownStore, _fmt, _parse


@pytest.fixture
def store_file(tmp_path: Path) -> Path:
    return tmp_path / "cooldown.json"


@pytest.fixture
def store(store_file: Path) -> CooldownStore:
    return CooldownStore(str(store_file))


def _past(seconds: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    return _fmt(dt)


def test_empty_store_has_no_jobs(store: CooldownStore) -> None:
    assert store.all_jobs() == []


def test_last_alert_unknown_job_returns_none(store: CooldownStore) -> None:
    assert store.last_alert("backup") is None


def test_record_alert_persists(store: CooldownStore, store_file: Path) -> None:
    store.record_alert("backup")
    raw = json.loads(store_file.read_text())
    assert "backup" in raw


def test_record_alert_returns_datetime(store: CooldownStore) -> None:
    result = store.record_alert("backup")
    assert isinstance(result, datetime)
    assert result.tzinfo == timezone.utc


def test_is_cooled_down_no_previous_alert(store: CooldownStore) -> None:
    assert store.is_cooled_down("nightly", cooldown_seconds=300) is True


def test_is_cooled_down_within_window(store: CooldownStore, store_file: Path) -> None:
    store_file.write_text(json.dumps({"nightly": _past(60)}))
    fresh = CooldownStore(str(store_file))
    assert fresh.is_cooled_down("nightly", cooldown_seconds=300) is False


def test_is_cooled_down_after_window(store: CooldownStore, store_file: Path) -> None:
    store_file.write_text(json.dumps({"nightly": _past(400)}))
    fresh = CooldownStore(str(store_file))
    assert fresh.is_cooled_down("nightly", cooldown_seconds=300) is True


def test_reset_removes_job(store: CooldownStore) -> None:
    store.record_alert("cleanup")
    store.reset("cleanup")
    assert store.last_alert("cleanup") is None
    assert "cleanup" not in store.all_jobs()


def test_all_jobs_sorted(store: CooldownStore) -> None:
    for name in ["zebra", "alpha", "mango"]:
        store.record_alert(name)
    assert store.all_jobs() == ["alpha", "mango", "zebra"]


def test_corrupt_file_returns_empty_store(store_file: Path) -> None:
    store_file.write_text("not valid json{{")
    s = CooldownStore(str(store_file))
    assert s.all_jobs() == []
