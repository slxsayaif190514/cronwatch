"""Tests for JobTracker state management."""

import json
import os
import tempfile
from datetime import datetime

import pytest

from cronwatch.tracker import JobState, JobTracker


@pytest.fixture
def tmp_state_file(tmp_path):
    return str(tmp_path / "state.json")


@pytest.fixture
def tracker(tmp_state_file):
    return JobTracker(state_file=tmp_state_file)


def test_get_state_creates_empty(tracker):
    state = tracker.get_state("backup")
    assert state.job_name == "backup"
    assert state.last_run is None
    assert state.consecutive_failures == 0


def test_record_run_success(tracker):
    t = datetime(2024, 1, 10, 12, 0, 0)
    tracker.record_run("backup", "success", run_time=t)
    state = tracker.get_state("backup")
    assert state.last_status == "success"
    assert state.last_run_dt() == t
    assert state.consecutive_failures == 0


def test_record_run_failure_increments(tracker):
    tracker.record_run("backup", "failure")
    tracker.record_run("backup", "failure")
    state = tracker.get_state("backup")
    assert state.consecutive_failures == 2


def test_record_run_success_resets_failures(tracker):
    tracker.record_run("backup", "failure")
    tracker.record_run("backup", "failure")
    tracker.record_run("backup", "success")
    assert tracker.get_state("backup").consecutive_failures == 0


def test_record_alert_sent(tracker):
    t = datetime(2024, 1, 10, 12, 5, 0)
    tracker.record_alert_sent("backup", sent_at=t)
    state = tracker.get_state("backup")
    assert state.last_alert_sent_dt() == t


def test_state_persists_to_disk(tmp_state_file):
    t1 = JobTracker(state_file=tmp_state_file)
    t1.record_run("myjob", "success")

    t2 = JobTracker(state_file=tmp_state_file)
    state = t2.get_state("myjob")
    assert state.last_status == "success"


def test_all_states_returns_all(tracker):
    tracker.record_run("job_a", "success")
    tracker.record_run("job_b", "failure")
    states = tracker.all_states()
    assert "job_a" in states
    assert "job_b" in states
