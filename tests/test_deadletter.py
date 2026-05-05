"""Tests for cronwatch.deadletter."""

import pytest
from cronwatch.deadletter import DeadLetter, DeadLetterQueue


@pytest.fixture
def dlq_file(tmp_path):
    return str(tmp_path / "deadletter.json")


@pytest.fixture
def dlq(dlq_file):
    return DeadLetterQueue(dlq_file)


def test_empty_queue_returns_no_entries(dlq):
    assert dlq.all() == []


def test_push_persists_entry(dlq, dlq_file):
    dlq.push("backup", "email", "backup overdue", "connection refused")
    reloaded = DeadLetterQueue(dlq_file)
    entries = reloaded.all()
    assert len(entries) == 1
    assert entries[0].job_name == "backup"
    assert entries[0].channel == "email"
    assert entries[0].message == "backup overdue"
    assert entries[0].last_error == "connection refused"
    assert entries[0].attempts == 1


def test_push_multiple_entries(dlq):
    dlq.push("job_a", "slack", "msg1", "err1")
    dlq.push("job_b", "email", "msg2", "err2")
    assert len(dlq.all()) == 2


def test_remove_existing_entry(dlq):
    dlq.push("backup", "email", "msg", "err")
    removed = dlq.remove("backup", "email")
    assert removed is True
    assert dlq.all() == []


def test_remove_nonexistent_returns_false(dlq):
    result = dlq.remove("ghost", "email")
    assert result is False


def test_remove_persists_to_disk(dlq, dlq_file):
    dlq.push("backup", "email", "msg", "err")
    dlq.remove("backup", "email")
    reloaded = DeadLetterQueue(dlq_file)
    assert reloaded.all() == []


def test_increment_attempt_updates_count(dlq):
    dlq.push("backup", "email", "msg", "first error")
    dlq.increment_attempt("backup", "email", "second error")
    entry = dlq.all()[0]
    assert entry.attempts == 2
    assert entry.last_error == "second error"


def test_increment_persists_to_disk(dlq, dlq_file):
    dlq.push("backup", "email", "msg", "err")
    dlq.increment_attempt("backup", "email", "new err")
    reloaded = DeadLetterQueue(dlq_file)
    assert reloaded.all()[0].attempts == 2


def test_clear_removes_all_entries(dlq):
    dlq.push("job_a", "slack", "m1", "e1")
    dlq.push("job_b", "email", "m2", "e2")
    dlq.clear()
    assert dlq.all() == []


def test_dead_letter_to_dict_round_trip():
    entry = DeadLetter(
        job_name="nightly",
        channel="webhook",
        message="nightly failed",
        failed_at="2024-06-01T12:00:00Z",
        attempts=3,
        last_error="timeout",
    )
    restored = DeadLetter.from_dict(entry.to_dict())
    assert restored.job_name == entry.job_name
    assert restored.attempts == entry.attempts
    assert restored.last_error == entry.last_error
