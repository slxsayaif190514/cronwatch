"""Tests for cronwatch.burst_cmd."""

from __future__ import annotations

import argparse
import json

import pytest

from cronwatch.burst import BurstStore
from cronwatch.burst_cmd import build_parser, cmd_show, cmd_reset


@pytest.fixture
def bfile(tmp_path):
    return str(tmp_path / "burst.json")


def _ns(bfile, cmd, job=None, window=3600, max_runs=10):
    return argparse.Namespace(file=bfile, cmd=cmd, job=job, window=window, max_runs=max_runs)


def test_cmd_show_empty(bfile, capsys):
    cmd_show(_ns(bfile, "show"))
    out = capsys.readouterr().out
    assert "No burst data" in out


def test_cmd_show_all_jobs(bfile, capsys):
    s = BurstStore(bfile)
    for _ in range(3):
        s.record("daily")
    cmd_show(_ns(bfile, "show"))
    out = capsys.readouterr().out
    assert "daily" in out
    assert "3" in out


def test_cmd_show_single_job(bfile, capsys):
    s = BurstStore(bfile)
    s.record("alpha")
    s.record("beta")
    cmd_show(_ns(bfile, "show", job="alpha"))
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" not in out


def test_cmd_show_flags_bursting(bfile, capsys):
    s = BurstStore(bfile)
    for _ in range(6):
        s.record("flood")
    cmd_show(_ns(bfile, "show", max_runs=5))
    out = capsys.readouterr().out
    assert "YES" in out


def test_cmd_reset_single_job(bfile, capsys):
    s = BurstStore(bfile)
    s.record("report")
    cmd_reset(_ns(bfile, "reset", job="report"))
    out = capsys.readouterr().out
    assert "report" in out
    assert BurstStore(bfile).get_count("report") == 0


def test_cmd_reset_all_jobs(bfile, capsys):
    s = BurstStore(bfile)
    s.record("a")
    s.record("b")
    cmd_reset(_ns(bfile, "reset"))
    out = capsys.readouterr().out
    assert "cleared" in out
    assert BurstStore(bfile).all_jobs() == []


def test_build_parser_returns_parser():
    p = build_parser()
    ns = p.parse_args(["show"])
    assert ns.cmd == "show"
    assert ns.window == 3600
    assert ns.max_runs == 10
