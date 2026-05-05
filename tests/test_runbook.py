"""Tests for runbook store and CLI commands."""

from __future__ import annotations

import pytest
import argparse

from cronwatch.runbook import RunbookStore
from cronwatch.runbook_cmd import cmd_set, cmd_show, cmd_remove


@pytest.fixture
def rb_file(tmp_path):
    return str(tmp_path / "runbook.json")


@pytest.fixture
def store(rb_file):
    return RunbookStore(rb_file)


def _ns(**kwargs):
    defaults = {"file": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_empty_store_returns_no_entries(store):
    assert store.all() == []


def test_get_unknown_job_returns_none(store):
    assert store.get("missing_job") is None


def test_set_persists_entry(store):
    entry = store.set("backup", "https://wiki.example.com/backup", notes="Run daily")
    assert entry.job_name == "backup"
    assert entry.url == "https://wiki.example.com/backup"
    assert entry.notes == "Run daily"
    assert entry.updated_at != ""


def test_set_overwrites_existing(store):
    store.set("backup", "https://old.example.com")
    store.set("backup", "https://new.example.com", notes="Updated")
    entry = store.get("backup")
    assert entry.url == "https://new.example.com"
    assert entry.notes == "Updated"


def test_remove_returns_true_on_success(store):
    store.set("cleanup", "https://wiki.example.com/cleanup")
    assert store.remove("cleanup") is True
    assert store.get("cleanup") is None


def test_remove_returns_false_for_missing(store):
    assert store.remove("nonexistent") is False


def test_all_returns_sorted(store):
    store.set("zebra_job", "https://example.com/z")
    store.set("alpha_job", "https://example.com/a")
    names = [e.job_name for e in store.all()]
    assert names == ["alpha_job", "zebra_job"]


def test_store_reloads_from_disk(rb_file):
    s1 = RunbookStore(rb_file)
    s1.set("disk_job", "https://example.com/disk")
    s2 = RunbookStore(rb_file)
    entry = s2.get("disk_job")
    assert entry is not None
    assert entry.url == "https://example.com/disk"


def test_cmd_set_creates_entry(rb_file, capsys):
    args = _ns(file=rb_file, job="myjob", url="https://wiki/myjob", notes="")
    cmd_set(args)
    out = capsys.readouterr().out
    assert "myjob" in out
    assert "https://wiki/myjob" in out


def test_cmd_remove_missing_exits(rb_file):
    args = _ns(file=rb_file, job="ghost")
    with pytest.raises(SystemExit):
        cmd_remove(args)
