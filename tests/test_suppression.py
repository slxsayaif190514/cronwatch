"""Tests for cronwatch.suppression."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.suppression import SuppressionStore


def _utc(**kwargs) -> datetime:
    return datetime.now(timezone.utc) + timedelta(**kwargs)


@pytest.fixture
def store_file(tmp_path: Path) -> Path:
    return tmp_path / "suppression.json"


@pytest.fixture
def store(store_file: Path) -> SuppressionStore:
    return SuppressionStore(store_file)


def test_empty_store_has_no_rules(store: SuppressionStore) -> None:
    assert store.all_rules() == []
    assert store.active_rules() == []


def test_is_suppressed_unknown_job_returns_false(store: SuppressionStore) -> None:
    assert store.is_suppressed("missing_job") is False


def test_add_rule_persists(store_file: Path) -> None:
    s = SuppressionStore(store_file)
    s.add("backup", "planned maintenance")
    s2 = SuppressionStore(store_file)
    assert len(s2.all_rules()) == 1
    assert s2.all_rules()[0].job_name == "backup"


def test_add_without_expiry_is_always_active(store: SuppressionStore) -> None:
    store.add("job_a", "no expiry")
    assert store.is_suppressed("job_a") is True


def test_add_with_future_expiry_is_active(store: SuppressionStore) -> None:
    store.add("job_b", "future", expires_at=_utc(hours=2))
    assert store.is_suppressed("job_b") is True


def test_add_with_past_expiry_is_not_active(store: SuppressionStore) -> None:
    past = _utc(hours=-1)
    store.add("job_c", "expired", expires_at=past)
    assert store.is_suppressed("job_c") is False


def test_remove_existing_rule(store: SuppressionStore) -> None:
    store.add("job_d", "reason")
    removed = store.remove("job_d")
    assert removed == 1
    assert store.is_suppressed("job_d") is False


def test_remove_unknown_job_returns_zero(store: SuppressionStore) -> None:
    assert store.remove("nonexistent") == 0


def test_active_rules_excludes_expired(store: SuppressionStore) -> None:
    store.add("live", "active", expires_at=_utc(hours=1))
    store.add("dead", "expired", expires_at=_utc(hours=-1))
    active = store.active_rules()
    names = [r.job_name for r in active]
    assert "live" in names
    assert "dead" not in names


def test_purge_expired_removes_only_expired(store: SuppressionStore) -> None:
    store.add("keep", "active", expires_at=_utc(hours=1))
    store.add("drop", "expired", expires_at=_utc(hours=-1))
    purged = store.purge_expired()
    assert purged == 1
    remaining = [r.job_name for r in store.all_rules()]
    assert "keep" in remaining
    assert "drop" not in remaining


def test_multiple_rules_same_job(store: SuppressionStore) -> None:
    store.add("multi", "first")
    store.add("multi", "second")
    assert store.is_suppressed("multi") is True
    removed = store.remove("multi")
    assert removed == 2
