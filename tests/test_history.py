"""Tests for cronwatch.history module."""

import os
import pytest
from datetime import datetime

from cronwatch.history import JobHistory, RunRecord


@pytest.fixture
def history_file(tmp_path):
    return str(tmp_path / "history.json")


@pytest.fixture
def history(history_file):
    return JobHistory(history_file)


def _record(job="backup", success=True, duration=10.0, dt=None):
    return RunRecord(
        job_name=job,
        started_at=dt or datetime(2024, 1, 1, 12, 0, 0),
        success=success,
        duration_s=duration,
    )


def test_empty_history_returns_no_records(history):
    assert history.get_records("backup") == []


def test_record_persists_to_disk(history_file):
    h = JobHistory(history_file)
    h.record(_record())
    h2 = JobHistory(history_file)
    assert len(h2.get_records("backup")) == 1


def test_record_roundtrip(history):
    r = _record(duration=42.5)
    history.record(r)
    records = history.get_records("backup")
    assert len(records) == 1
    assert records[0].duration_s == 42.5
    assert records[0].success is True


def test_get_records_filters_by_job(history):
    history.record(_record(job="backup"))
    history.record(_record(job="cleanup"))
    assert len(history.get_records("backup")) == 1
    assert len(history.get_records("cleanup")) == 1


def test_last_success_returns_most_recent(history):
    history.record(_record(success=False, dt=datetime(2024, 1, 1, 10, 0)))
    history.record(_record(success=True, dt=datetime(2024, 1, 1, 11, 0)))
    history.record(_record(success=True, dt=datetime(2024, 1, 1, 12, 0)))
    result = history.last_success("backup")
    assert result is not None
    assert result.started_at == datetime(2024, 1, 1, 12, 0)


def test_last_success_none_when_all_failed(history):
    history.record(_record(success=False))
    assert history.last_success("backup") is None


def test_average_duration(history):
    history.record(_record(duration=10.0))
    history.record(_record(duration=20.0))
    history.record(_record(duration=30.0))
    assert history.average_duration("backup") == 20.0


def test_average_duration_ignores_failures(history):
    history.record(_record(success=True, duration=10.0))
    history.record(_record(success=False, duration=999.0))
    assert history.average_duration("backup") == 10.0


def test_max_records_trimmed(history_file):
    h = JobHistory(history_file, max_records=5)
    for i in range(10):
        h.record(_record(dt=datetime(2024, 1, 1, i, 0)))
    assert len(h.get_records("backup")) == 5
