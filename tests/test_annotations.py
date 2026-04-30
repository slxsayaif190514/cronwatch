"""Tests for cronwatch.annotations."""

import pytest
from datetime import datetime, timezone

from cronwatch.annotations import Annotation, AnnotationStore


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "annotations.json")


@pytest.fixture
def store(store_file):
    return AnnotationStore(store_file)


def test_empty_store_returns_no_annotations(store):
    assert store.all() == []


def test_add_annotation_persists(store, store_file):
    store.add("backup", "Ran manually after failure", author="alice")
    reloaded = AnnotationStore(store_file)
    entries = reloaded.get("backup")
    assert len(entries) == 1
    assert entries[0].note == "Ran manually after failure"
    assert entries[0].author == "alice"


def test_get_filters_by_job(store):
    store.add("backup", "note 1")
    store.add("cleanup", "note 2")
    store.add("backup", "note 3")
    results = store.get("backup")
    assert len(results) == 2
    assert all(r.job_name == "backup" for r in results)


def test_all_returns_every_entry(store):
    store.add("backup", "a")
    store.add("cleanup", "b")
    assert len(store.all()) == 2


def test_clear_removes_only_matching(store):
    store.add("backup", "note")
    store.add("cleanup", "note")
    removed = store.clear("backup")
    assert removed == 1
    assert store.get("backup") == []
    assert len(store.get("cleanup")) == 1


def test_clear_returns_zero_if_nothing_to_remove(store):
    assert store.clear("nonexistent") == 0


def test_annotation_roundtrip():
    ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    ann = Annotation("myjob", "test note", author="bot", created_at=ts)
    d = ann.to_dict()
    restored = Annotation.from_dict(d)
    assert restored.job_name == "myjob"
    assert restored.note == "test note"
    assert restored.author == "bot"
    assert restored.created_at == ts


def test_default_author_is_system(store):
    ann = store.add("myjob", "hello")
    assert ann.author == "system"
