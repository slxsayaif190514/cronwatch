"""Tests for cronwatch.fingerprint."""

from __future__ import annotations

import pytest

from cronwatch.fingerprint import FingerprintStore, fingerprint_error


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "fingerprints.json")


@pytest.fixture
def store(store_file):
    return FingerprintStore(store_file)


def test_fingerprint_error_is_deterministic():
    fp1 = fingerprint_error("Connection refused")
    fp2 = fingerprint_error("Connection refused")
    assert fp1 == fp2


def test_fingerprint_error_normalizes_whitespace():
    fp1 = fingerprint_error("Connection  refused")
    fp2 = fingerprint_error("connection refused")
    assert fp1 == fp2


def test_fingerprint_error_different_messages_differ():
    fp1 = fingerprint_error("timeout exceeded")
    fp2 = fingerprint_error("disk full")
    assert fp1 != fp2


def test_fingerprint_error_returns_12_chars():
    fp = fingerprint_error("some error")
    assert len(fp) == 12


def test_empty_store_returns_no_entries(store):
    assert store.get_all() == []


def test_record_persists_entry(store, store_file):
    store.record("backup", "Connection refused")
    store2 = FingerprintStore(store_file)
    entries = store2.get_all()
    assert len(entries) == 1
    assert entries[0].job == "backup"
    assert entries[0].count == 1


def test_record_same_error_increments_count(store):
    store.record("backup", "Connection refused")
    store.record("backup", "Connection refused")
    entries = store.get_all(job="backup")
    assert len(entries) == 1
    assert entries[0].count == 2


def test_record_different_errors_creates_separate_entries(store):
    store.record("backup", "Connection refused")
    store.record("backup", "Disk full")
    entries = store.get_all(job="backup")
    assert len(entries) == 2


def test_get_filters_by_job(store):
    store.record("backup", "timeout")
    store.record("sync", "timeout")
    backup_entries = store.get_all(job="backup")
    assert all(e.job == "backup" for e in backup_entries)
    assert len(backup_entries) == 1


def test_get_returns_entry_by_fingerprint(store):
    entry = store.record("backup", "Connection refused")
    found = store.get("backup", entry.fingerprint)
    assert found is not None
    assert found.fingerprint == entry.fingerprint


def test_get_unknown_fingerprint_returns_none(store):
    assert store.get("backup", "000000000000") is None


def test_reset_removes_entry(store):
    entry = store.record("backup", "timeout")
    ok = store.reset("backup", entry.fingerprint)
    assert ok is True
    assert store.get("backup", entry.fingerprint) is None


def test_reset_unknown_returns_false(store):
    ok = store.reset("backup", "deadbeef0000")
    assert ok is False
