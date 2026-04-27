"""Tests for cronwatch.silence."""

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from cronwatch.silence import SilenceStore, SilenceWindow


def _utc(**kwargs) -> datetime:
    return datetime.now(timezone.utc) + timedelta(**kwargs)


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "silence.json")


@pytest.fixture
def store(store_file):
    return SilenceStore(store_file)


def test_empty_store_not_silenced(store):
    assert store.is_silenced("backup") is False


def test_add_active_window_silences_job(store):
    w = SilenceWindow("backup", _utc(minutes=-5), _utc(minutes=55), "maintenance")
    store.add(w)
    assert store.is_silenced("backup") is True


def test_expired_window_does_not_silence(store):
    w = SilenceWindow("backup", _utc(hours=-2), _utc(hours=-1))
    store.add(w)
    assert store.is_silenced("backup") is False


def test_future_window_does_not_silence(store):
    w = SilenceWindow("backup", _utc(hours=1), _utc(hours=2))
    store.add(w)
    assert store.is_silenced("backup") is False


def test_silence_is_job_specific(store):
    w = SilenceWindow("backup", _utc(minutes=-5), _utc(minutes=55))
    store.add(w)
    assert store.is_silenced("reports") is False


def test_persists_to_disk(store, store_file):
    w = SilenceWindow("backup", _utc(minutes=-5), _utc(minutes=55), "deploy")
    store.add(w)
    store2 = SilenceStore(store_file)
    assert store2.is_silenced("backup") is True
    assert store2.all_windows()[0].reason == "deploy"


def test_remove_expired_cleans_old_windows(store):
    store.add(SilenceWindow("a", _utc(hours=-3), _utc(hours=-1)))
    store.add(SilenceWindow("b", _utc(minutes=-5), _utc(minutes=55)))
    removed = store.remove_expired()
    assert removed == 1
    assert len(store.all_windows()) == 1
    assert store.all_windows()[0].job_name == "b"


def test_remove_expired_persists(store, store_file):
    store.add(SilenceWindow("old", _utc(hours=-3), _utc(hours=-1)))
    store.remove_expired()
    with open(store_file) as f:
        data = json.load(f)
    assert data == []


def test_is_active_with_explicit_time():
    now = datetime.now(timezone.utc)
    w = SilenceWindow("x", now - timedelta(hours=1), now + timedelta(hours=1))
    assert w.is_active(now) is True
    assert w.is_active(now + timedelta(hours=2)) is False
