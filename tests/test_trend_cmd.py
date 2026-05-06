"""Tests for cronwatch.trend_cmd."""

from __future__ import annotations

import argparse
import pytest

from cronwatch.trend import TrendStore
from cronwatch.trend_cmd import cmd_show, cmd_reset, build_parser


@pytest.fixture
def tfile(tmp_path):
    return str(tmp_path / "trend.json")


def _ns(tfile, cmd, job=None, threshold=1.0):
    ns = argparse.Namespace(file=tfile, cmd=cmd, job=job, threshold=threshold)
    return ns


def test_cmd_show_empty(tfile, capsys):
    cmd_show(_ns(tfile, "show"))
    out = capsys.readouterr().out
    assert "No trend data" in out


def test_cmd_show_single_job(tfile, capsys):
    s = TrendStore(tfile)
    for i in range(3):
        s.record("nightly", float(i * 5))
    cmd_show(_ns(tfile, "show", job="nightly"))
    out = capsys.readouterr().out
    assert "nightly" in out
    assert "samples=3" in out


def test_cmd_show_trending_flag(tfile, capsys):
    s = TrendStore(tfile)
    for i in range(5):
        s.record("nightly", float(i * 50))
    cmd_show(_ns(tfile, "show", threshold=1.0))
    out = capsys.readouterr().out
    assert "TRENDING UP" in out


def test_cmd_reset_single_job(tfile, capsys):
    s = TrendStore(tfile)
    s.record("job_a", 10.0)
    s.record("job_b", 20.0)
    cmd_reset(_ns(tfile, "reset", job="job_a"))
    s2 = TrendStore(tfile)
    assert s2.get_points("job_a") == []
    assert len(s2.get_points("job_b")) == 1


def test_cmd_reset_all(tfile, capsys):
    s = TrendStore(tfile)
    s.record("job_a", 5.0)
    s.record("job_b", 5.0)
    cmd_reset(_ns(tfile, "reset"))
    s2 = TrendStore(tfile)
    assert s2.get_points("job_a") == []
    assert s2.get_points("job_b") == []


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)
