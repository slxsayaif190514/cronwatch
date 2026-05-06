"""Tests for cronwatch.checkpoint_cmd."""

from __future__ import annotations

import argparse

import pytest

from cronwatch.checkpoint import CheckpointStore
from cronwatch.checkpoint_cmd import cmd_show, cmd_set, cmd_remove, build_parser


@pytest.fixture
def cfile(tmp_path):
    return str(tmp_path / "cp.json")


def _ns(file, **kw):
    base = {"file": file, "job": None}
    base.update(kw)
    return argparse.Namespace(**base)


def test_cmd_show_empty(cfile, capsys):
    cmd_show(_ns(cfile))
    out = capsys.readouterr().out
    assert "No checkpoints" in out


def test_cmd_set_creates_checkpoint(cfile, capsys):
    cmd_set(_ns(cfile, job="backup"))
    out = capsys.readouterr().out
    assert "backup" in out
    assert "Checkpoint set" in out
    store = CheckpointStore(cfile)
    assert store.get("backup") is not None


def test_cmd_show_all_jobs(cfile, capsys):
    store = CheckpointStore(cfile)
    store.set("job_a")
    store.set("job_b")
    cmd_show(_ns(cfile))
    out = capsys.readouterr().out
    assert "job_a" in out
    assert "job_b" in out


def test_cmd_show_single_job(cfile, capsys):
    store = CheckpointStore(cfile)
    store.set("only")
    cmd_show(_ns(cfile, job="only"))
    out = capsys.readouterr().out
    assert "only" in out


def test_cmd_show_missing_job(cfile, capsys):
    cmd_show(_ns(cfile, job="ghost"))
    out = capsys.readouterr().out
    assert "no checkpoint" in out


def test_cmd_remove_existing(cfile, capsys):
    store = CheckpointStore(cfile)
    store.set("todelete")
    cmd_remove(_ns(cfile, job="todelete"))
    out = capsys.readouterr().out
    assert "removed" in out
    assert store.get("todelete") is None


def test_cmd_remove_missing_exits_one(cfile):
    with pytest.raises(SystemExit) as exc:
        cmd_remove(_ns(cfile, job="ghost"))
    assert exc.value.code == 1


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)
