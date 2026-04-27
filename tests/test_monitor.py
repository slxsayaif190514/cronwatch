"""Tests for the monitor check loop."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import AlertConfig, Config, JobConfig
from cronwatch.monitor import _should_alert, run_checks
from cronwatch.tracker import JobState, JobTracker


def make_config(schedule="* * * * *", grace=2, failure_threshold=3):
    job = JobConfig(
        name="test_job",
        schedule=schedule,
        grace_minutes=grace,
        failure_threshold=failure_threshold,
    )
    alerts = AlertConfig(
        email="ops@example.com",
        webhook_url=None,
        cooldown_minutes=30,
    )
    return Config(jobs=[job], alerts=alerts)


@pytest.fixture
def tracker(tmp_path):
    return JobTracker(state_file=str(tmp_path / "state.json"))


def test_should_alert_no_previous_alert():
    state = JobState(job_name="j")
    assert _should_alert(state, datetime.utcnow(), 30) is True


def test_should_alert_within_cooldown():
    state = JobState(job_name="j", last_alert_sent="2024-01-10T12:00:00")
    now = datetime.fromisoformat("2024-01-10T12:10:00")
    assert _should_alert(state, now, 30) is False


def test_should_alert_after_cooldown():
    state = JobState(job_name="j", last_alert_sent="2024-01-10T12:00:00")
    now = datetime.fromisoformat("2024-01-10T12:31:00")
    assert _should_alert(state, now, 30) is True


@patch("cronwatch.monitor.send_alert", return_value=True)
def test_overdue_triggers_alert(mock_send, tracker):
    config = make_config(schedule="* * * * *", grace=1)
    # job has never run; pick a time well past expected
    now = datetime(2024, 1, 10, 12, 5, 0)
    run_checks(config, tracker, now=now)
    mock_send.assert_called_once()


@patch("cronwatch.monitor.send_alert", return_value=True)
def test_failure_threshold_triggers_alert(mock_send, tracker):
    config = make_config(failure_threshold=2)
    tracker.record_run("test_job", "failure")
    tracker.record_run("test_job", "failure")
    now = datetime(2024, 1, 10, 12, 0, 30)
    run_checks(config, tracker, now=now)
    assert mock_send.called


@patch("cronwatch.monitor.send_alert", return_value=True)
def test_no_alert_during_cooldown(mock_send, tracker):
    config = make_config(schedule="* * * * *", grace=1)
    now = datetime(2024, 1, 10, 12, 5, 0)
    # Simulate alert already sent 5 minutes ago
    tracker.record_alert_sent("test_job", sent_at=datetime(2024, 1, 10, 12, 0, 0))
    run_checks(config, tracker, now=now)
    mock_send.assert_not_called()
