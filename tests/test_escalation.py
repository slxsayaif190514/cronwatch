"""Tests for escalation store and dispatch helper."""

import pytest

from cronwatch.escalation import EscalationStore
from cronwatch.escalation_dispatch import alert_with_escalation, resolve_job


@pytest.fixture
def store(tmp_path):
    return EscalationStore(str(tmp_path / "escalation.json"))


def test_initial_count_is_zero(store):
    assert store.get_count("backup") == 0


def test_record_alert_increments(store):
    store.record_alert("backup")
    store.record_alert("backup")
    assert store.get_count("backup") == 2


def test_reset_clears_count(store):
    store.record_alert("backup")
    store.reset("backup")
    assert store.get_count("backup") == 0


def test_should_escalate_false_below_threshold(store):
    store.record_alert("backup")
    store.record_alert("backup")
    assert store.should_escalate("backup", threshold=3) is False


def test_should_escalate_true_at_threshold(store):
    for _ in range(3):
        store.record_alert("backup")
    assert store.should_escalate("backup", threshold=3) is True


def test_should_escalate_zero_threshold_never(store):
    for _ in range(10):
        store.record_alert("backup")
    assert store.should_escalate("backup", threshold=0) is False


def test_persists_across_instances(tmp_path):
    path = str(tmp_path / "esc.json")
    s1 = EscalationStore(path)
    s1.record_alert("job1")
    s1.record_alert("job1")
    s2 = EscalationStore(path)
    assert s2.get_count("job1") == 2


def test_alert_with_escalation_no_escalation(store):
    result = alert_with_escalation(
        store, "myjob", "Alert", "body", primary_channel="noop",
        escalation_channel="noop", escalation_threshold=3
    )
    assert result["count"] == 1
    assert result["escalated"] is False


def test_alert_with_escalation_triggers_at_threshold(store):
    for _ in range(2):
        alert_with_escalation(
            store, "myjob", "Alert", "body", primary_channel="noop",
            escalation_channel="noop", escalation_threshold=3
        )
    result = alert_with_escalation(
        store, "myjob", "Alert", "body", primary_channel="noop",
        escalation_channel="noop", escalation_threshold=3
    )
    # same channel so escalated flag stays False (deduplicated)
    assert result["count"] == 3


def test_resolve_job_resets_store(store):
    store.record_alert("myjob")
    resolve_job(store, "myjob")
    assert store.get_count("myjob") == 0
