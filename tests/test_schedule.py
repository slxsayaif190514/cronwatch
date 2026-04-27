from datetime import datetime, timezone, timedelta
import pytest
from cronwatch.schedule import get_last_expected_run, get_next_expected_run, is_overdue


NOW = datetime(2024, 6, 15, 12, 10, 0, tzinfo=timezone.utc)


def test_get_last_expected_run_every_minute():
    result = get_last_expected_run("* * * * *", now=NOW)
    assert result == datetime(2024, 6, 15, 12, 10, 0, tzinfo=timezone.utc)


def test_get_last_expected_run_hourly():
    result = get_last_expected_run("0 * * * *", now=NOW)
    assert result == datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


def test_get_next_expected_run_every_minute():
    result = get_next_expected_run("* * * * *", now=NOW)
    assert result == datetime(2024, 6, 15, 12, 11, 0, tzinfo=timezone.utc)


def test_get_next_expected_run_hourly():
    result = get_next_expected_run("0 * * * *", now=NOW)
    assert result == datetime(2024, 6, 15, 13, 0, 0, tzinfo=timezone.utc)


def test_is_overdue_never_ran_past_grace():
    # Expected at 12:00, now is 12:10 — 600s delay, grace is 300s
    assert is_overdue("0 * * * *", last_seen=None, max_delay_seconds=300, now=NOW) is True


def test_is_overdue_never_ran_within_grace():
    # Expected at 12:00, now is 12:10 — 600s delay, grace is 900s
    assert is_overdue("0 * * * *", last_seen=None, max_delay_seconds=900, now=NOW) is False


def test_is_overdue_ran_before_last_slot_past_grace():
    last_seen = datetime(2024, 6, 15, 11, 0, 0, tzinfo=timezone.utc)
    assert is_overdue("0 * * * *", last_seen=last_seen, max_delay_seconds=300, now=NOW) is True


def test_is_overdue_ran_in_current_slot():
    last_seen = datetime(2024, 6, 15, 12, 1, 0, tzinfo=timezone.utc)
    assert is_overdue("0 * * * *", last_seen=last_seen, max_delay_seconds=300, now=NOW) is False


def test_is_overdue_ran_exactly_at_slot():
    last_seen = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    assert is_overdue("0 * * * *", last_seen=last_seen, max_delay_seconds=300, now=NOW) is False
