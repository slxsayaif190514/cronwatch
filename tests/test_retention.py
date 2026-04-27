"""Tests for cronwatch.retention."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from cronwatch.retention import prune_history, prune_digest, run_retention


def _make_record(record_id: str, days_ago: float):
    rec = MagicMock()
    rec.id = record_id
    rec.started_at = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    return rec


# ---------------------------------------------------------------------------
# prune_history
# ---------------------------------------------------------------------------

def test_prune_history_removes_old_records():
    store = MagicMock()
    store.get_records.return_value = [
        _make_record("a", 10),
        _make_record("b", 3),
        _make_record("c", 1),
    ]
    removed = prune_history(store, max_age_days=7)
    assert removed == 1
    store.delete_record.assert_called_once_with("a")


def test_prune_history_filters_by_job_name():
    store = MagicMock()
    store.get_records.return_value = [_make_record("x", 20)]
    removed = prune_history(store, max_age_days=5, job_name="myjob")
    store.get_records.assert_called_once_with("myjob")
    assert removed == 1


def test_prune_history_no_old_records():
    store = MagicMock()
    store.get_records.return_value = [_make_record("a", 1)]
    removed = prune_history(store, max_age_days=30)
    assert removed == 0
    store.delete_record.assert_not_called()


def test_prune_history_invalid_age_raises():
    store = MagicMock()
    with pytest.raises(ValueError):
        prune_history(store, max_age_days=0)


# ---------------------------------------------------------------------------
# prune_digest
# ---------------------------------------------------------------------------

def _iso(days_ago: float) -> str:
    return (datetime.now(tz=timezone.utc) - timedelta(days=days_ago)).isoformat()


def test_prune_digest_removes_old_events():
    store = MagicMock()
    store.get_events.return_value = [
        {"timestamp": _iso(10), "msg": "old"},
        {"timestamp": _iso(1), "msg": "recent"},
    ]
    removed = prune_digest(store, max_age_days=7)
    assert removed == 1
    store.clear.assert_called_once()
    store.add_event.assert_called_once_with({"timestamp": store.get_events.return_value[1]["timestamp"], "msg": "recent"})


def test_prune_digest_nothing_to_prune():
    store = MagicMock()
    store.get_events.return_value = [{"timestamp": _iso(1), "msg": "ok"}]
    removed = prune_digest(store, max_age_days=30)
    assert removed == 0
    store.clear.assert_not_called()


def test_prune_digest_invalid_age_raises():
    store = MagicMock()
    with pytest.raises(ValueError):
        prune_digest(store, max_age_days=-1)


# ---------------------------------------------------------------------------
# run_retention
# ---------------------------------------------------------------------------

def test_run_retention_returns_summary():
    history = MagicMock()
    history.get_records.return_value = [_make_record("z", 100)]
    digest = MagicMock()
    digest.get_events.return_value = [{"timestamp": _iso(50), "msg": "x"}]

    result = run_retention(history, digest, max_age_days=7)
    assert result["history_pruned"] == 1
    assert result["digest_pruned"] == 1
