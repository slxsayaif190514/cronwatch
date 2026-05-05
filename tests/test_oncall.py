"""Tests for cronwatch.oncall and oncall_cmd."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

import pytest

from cronwatch.oncall import OnCallEntry, OnCallStore


def _utc(year=2024, month=1, day=1, hour=0) -> datetime:
    return datetime(year, month, day, hour, tzinfo=timezone.utc)


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "oncall.json")


@pytest.fixture
def store(store_file):
    return OnCallStore(store_file)


def _make_entry(name="alice", email="alice@example.com", active=True) -> OnCallEntry:
    now = datetime.now(timezone.utc)
    if active:
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
    else:
        start = now - timedelta(days=2)
        end = now - timedelta(days=1)
    return OnCallEntry(name=name, email=email, start=start, end=end, tags=["backend"])


def test_empty_store_has_no_entries(store):
    assert store.all() == []


def test_add_entry_persists(store, store_file):
    entry = _make_entry()
    store.add(entry)
    store2 = OnCallStore(store_file)
    assert len(store2.all()) == 1
    assert store2.all()[0].name == "alice"


def test_get_active_returns_current(store):
    active = _make_entry(name="alice", active=True)
    inactive = _make_entry(name="bob", active=False)
    store.add(active)
    store.add(inactive)
    result = store.get_active()
    assert len(result) == 1
    assert result[0].name == "alice"


def test_get_active_filters_by_tag(store):
    e1 = _make_entry(name="alice")
    e1.tags = ["backend"]
    e2 = _make_entry(name="bob")
    e2.tags = ["frontend"]
    store.add(e1)
    store.add(e2)
    result = store.get_active(tag="frontend")
    assert len(result) == 1
    assert result[0].name == "bob"


def test_remove_existing_entry(store):
    store.add(_make_entry(name="alice"))
    removed = store.remove("alice")
    assert removed is True
    assert store.all() == []


def test_remove_nonexistent_returns_false(store):
    assert store.remove("nobody") is False


def test_is_active_respects_at_param():
    entry = OnCallEntry(
        name="carol",
        email="carol@example.com",
        start=_utc(2024, 6, 1),
        end=_utc(2024, 6, 7),
        tags=[],
    )
    assert entry.is_active(at=_utc(2024, 6, 3)) is True
    assert entry.is_active(at=_utc(2024, 7, 1)) is False


def test_roundtrip_serialization():
    entry = _make_entry()
    d = entry.to_dict()
    restored = OnCallEntry.from_dict(d)
    assert restored.name == entry.name
    assert restored.email == entry.email
    assert restored.tags == entry.tags
