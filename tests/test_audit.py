"""Tests for cronwatch.audit."""

import os
import pytest
from datetime import datetime, timezone

from cronwatch.audit import AuditLog, AuditEntry


@pytest.fixture
def log_file(tmp_path):
    return str(tmp_path / "audit.jsonl")


@pytest.fixture
def log(log_file):
    return AuditLog(path=log_file)


def test_empty_log_returns_no_entries(log):
    assert log.read() == []


def test_append_persists_entry(log, log_file):
    log.append("alert_sent", job="backup", detail="overdue by 5m")
    assert os.path.exists(log_file)
    entries = log.read()
    assert len(entries) == 1
    e = entries[0]
    assert e.event == "alert_sent"
    assert e.job == "backup"
    assert e.detail == "overdue by 5m"


def test_append_returns_entry(log):
    entry = log.append("job_resolved", job="sync", detail="")
    assert isinstance(entry, AuditEntry)
    assert entry.event == "job_resolved"


def test_multiple_entries_appended(log):
    log.append("alert_sent", job="a")
    log.append("alert_sent", job="b")
    log.append("job_resolved", job="a")
    assert len(log.read()) == 3


def test_filter_by_job(log):
    log.append("alert_sent", job="backup")
    log.append("alert_sent", job="sync")
    log.append("job_resolved", job="backup")
    results = log.read(job="backup")
    assert len(results) == 2
    assert all(e.job == "backup" for e in results)


def test_filter_by_event(log):
    log.append("alert_sent", job="a")
    log.append("job_resolved", job="a")
    log.append("alert_sent", job="b")
    results = log.read(event="alert_sent")
    assert len(results) == 2
    assert all(e.event == "alert_sent" for e in results)


def test_filter_by_job_and_event(log):
    log.append("alert_sent", job="a")
    log.append("alert_sent", job="b")
    log.append("job_resolved", job="a")
    results = log.read(job="a", event="alert_sent")
    assert len(results) == 1
    assert results[0].job == "a"
    assert results[0].event == "alert_sent"


def test_clear_removes_all_entries(log):
    log.append("alert_sent", job="a")
    log.append("alert_sent", job="b")
    removed = log.clear()
    assert removed == 2
    assert log.read() == []


def test_clear_on_empty_log_returns_zero(log):
    assert log.clear() == 0


def test_entry_timestamp_is_utc(log):
    entry = log.append("test_event", job="x")
    assert entry.ts.tzinfo == timezone.utc


def test_no_job_entry(log):
    log.append("daemon_started", job=None, detail="pid=1234")
    entries = log.read()
    assert len(entries) == 1
    assert entries[0].job is None
