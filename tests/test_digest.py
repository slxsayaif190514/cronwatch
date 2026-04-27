"""Tests for cronwatch.digest DigestStore and build_digest."""

from __future__ import annotations

import json
import os
import pytest
from cronwatch.digest import DigestStore, build_digest


@pytest.fixture()
def store(tmp_path):
    return DigestStore(str(tmp_path / "digest.json"))


def test_empty_store_has_no_events(store):
    assert store.pending() == []


def test_add_event_persists(store):
    store.add_event("backup", "overdue", "missed window")
    assert len(store.pending()) == 1
    ev = store.pending()[0]
    assert ev["job"] == "backup"
    assert ev["kind"] == "overdue"
    assert ev["message"] == "missed window"
    assert "at" in ev


def test_add_multiple_events(store):
    store.add_event("job1", "overdue", "late")
    store.add_event("job2", "failure", "exit 1")
    assert len(store.pending()) == 2


def test_clear_removes_events(store):
    store.add_event("job1", "overdue", "late")
    store.clear()
    assert store.pending() == []


def test_store_reloads_from_disk(tmp_path):
    path = str(tmp_path / "digest.json")
    s1 = DigestStore(path)
    s1.add_event("job", "failure", "exit 2")
    s2 = DigestStore(path)
    assert len(s2.pending()) == 1
    assert s2.pending()[0]["job"] == "job"


def test_store_handles_corrupt_file(tmp_path):
    path = str(tmp_path / "digest.json")
    with open(path, "w") as fh:
        fh.write("not json{{")
    store = DigestStore(path)
    assert store.pending() == []


def test_build_digest_no_events():
    assert build_digest([]) == "No alerts to report."


def test_build_digest_formats_events():
    events = [
        {"at": "2024-01-01T00:00:00Z", "job": "backup", "kind": "overdue", "message": "late"},
        {"at": "2024-01-01T01:00:00Z", "job": "sync", "kind": "failure", "message": "exit 1"},
    ]
    result = build_digest(events)
    assert "2 alert" in result
    assert "backup" in result
    assert "sync" in result
    assert "overdue" in result
    assert "failure" in result
