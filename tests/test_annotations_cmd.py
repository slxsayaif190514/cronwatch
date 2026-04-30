"""Tests for cronwatch.annotations_cmd."""

import pytest

from cronwatch.annotations_cmd import main
from cronwatch.annotations import AnnotationStore


@pytest.fixture
def ann_path(tmp_path):
    return str(tmp_path / "ann.json")


def _ns(ann_path, *args):
    return ["--file", ann_path] + list(args)


def test_cmd_add_creates_annotation(ann_path):
    rc = main(_ns(ann_path, "add", "backup", "manually triggered"))
    assert rc == 0
    store = AnnotationStore(ann_path)
    entries = store.get("backup")
    assert len(entries) == 1
    assert entries[0].note == "manually triggered"


def test_cmd_add_with_author(ann_path):
    rc = main(_ns(ann_path, "add", "cleanup", "debug run", "--author", "devops"))
    assert rc == 0
    store = AnnotationStore(ann_path)
    assert store.get("cleanup")[0].author == "devops"


def test_cmd_list_all(ann_path, capsys):
    main(_ns(ann_path, "add", "backup", "note a"))
    main(_ns(ann_path, "add", "cleanup", "note b"))
    rc = main(_ns(ann_path, "list"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "backup" in out
    assert "cleanup" in out


def test_cmd_list_filtered(ann_path, capsys):
    main(_ns(ann_path, "add", "backup", "note a"))
    main(_ns(ann_path, "add", "cleanup", "note b"))
    rc = main(_ns(ann_path, "list", "backup"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "backup" in out
    assert "cleanup" not in out


def test_cmd_list_empty(ann_path, capsys):
    rc = main(_ns(ann_path, "list"))
    assert rc == 0
    assert "No annotations" in capsys.readouterr().out


def test_cmd_clear(ann_path):
    main(_ns(ann_path, "add", "backup", "note"))
    rc = main(_ns(ann_path, "clear", "backup"))
    assert rc == 0
    store = AnnotationStore(ann_path)
    assert store.get("backup") == []


def test_no_command_returns_one(ann_path):
    rc = main(["--file", ann_path])
    assert rc == 1
