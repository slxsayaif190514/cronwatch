"""Tests for cronwatch.throttle_cmd."""

from __future__ import annotations

import argparse
import json

import pytest

from cronwatch.throttle import ThrottleStore
from cronwatch.throttle_cmd import cmd_show, cmd_reset, build_parser


@pytest.fixture
def tfile(tmp_path):
    return str(tmp_path / "throttle.json")


def _ns(tfile, **kwargs) -> argparse.Namespace:
    defaults = {"file": tfile, "job": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_show_empty(tfile, capsys):
    cmd_show(_ns(tfile))
    out = capsys.readouterr().out
    assert "No throttle entries" in out


def test_cmd_show_all_jobs(tfile, capsys):
    s = ThrottleStore(path=tfile, window_seconds=3600, max_burst=5)
    s.record_alert("alpha")
    s.record_alert("alpha")
    s.record_alert("beta")

    cmd_show(_ns(tfile))
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_cmd_show_single_job(tfile, capsys):
    s = ThrottleStore(path=tfile, window_seconds=3600, max_burst=5)
    s.record_alert("alpha")
    s.record_alert("beta")

    cmd_show(_ns(tfile, job="alpha"))
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" not in out


def test_cmd_reset_single_job(tfile, capsys):
    s = ThrottleStore(path=tfile, window_seconds=3600, max_burst=5)
    s.record_alert("gamma")

    cmd_reset(_ns(tfile, job="gamma"))
    out = capsys.readouterr().out
    assert "gamma" in out

    s2 = ThrottleStore(path=tfile)
    assert s2.get_entry("gamma") is None


def test_cmd_reset_all(tfile, capsys):
    s = ThrottleStore(path=tfile, window_seconds=3600, max_burst=5)
    s.record_alert("x")
    s.record_alert("y")

    cmd_reset(_ns(tfile, job=None))
    out = capsys.readouterr().out
    assert "cleared" in out

    s2 = ThrottleStore(path=tfile)
    assert s2._data == {}


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None
    args = parser.parse_args(["show"])
    assert args.command == "show"
