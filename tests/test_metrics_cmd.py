"""Tests for cronwatch.metrics_cmd."""

import argparse
from pathlib import Path

import pytest

from cronwatch.metrics import MetricsStore
from cronwatch.metrics_cmd import build_parser, cmd_show, cmd_reset


@pytest.fixture
def mfile(tmp_path):
    return tmp_path / "metrics.json"


@pytest.fixture
def preloaded(mfile):
    s = MetricsStore(mfile)
    s.record("backup", success=True, duration_s=2.0)
    s.record("backup", success=False, duration_s=1.0)
    s.record("sync", success=True, duration_s=0.5)
    return mfile


def _ns(**kwargs):
    base = {"metrics_file": None, "job": None}
    base.update(kwargs)
    return argparse.Namespace(**base)


def test_cmd_show_all(preloaded, capsys):
    ns = _ns(metrics_file=str(preloaded))
    cmd_show(ns)
    out = capsys.readouterr().out
    assert "backup" in out
    assert "sync" in out


def test_cmd_show_single_job(preloaded, capsys):
    ns = _ns(metrics_file=str(preloaded), job="backup")
    cmd_show(ns)
    out = capsys.readouterr().out
    assert "backup" in out
    assert "sync" not in out


def test_cmd_show_no_metrics(mfile, capsys):
    ns = _ns(metrics_file=str(mfile))
    cmd_show(ns)
    out = capsys.readouterr().out
    assert "No metrics" in out


def test_cmd_reset_removes_job(preloaded, capsys):
    ns = _ns(metrics_file=str(preloaded), job="backup")
    cmd_reset(ns)
    store = MetricsStore(preloaded)
    assert store.get("backup").total_runs == 0
    out = capsys.readouterr().out
    assert "reset" in out.lower()


def test_build_parser_show():
    p = build_parser()
    ns = p.parse_args(["show"])
    assert ns.command == "show"
    assert ns.job is None


def test_build_parser_reset():
    p = build_parser()
    ns = p.parse_args(["reset", "myjob"])
    assert ns.command == "reset"
    assert ns.job == "myjob"
