"""Tests for cronwatch.baseline_cmd."""

from __future__ import annotations

import argparse
import pytest

from cronwatch.baseline import BaselineStore
from cronwatch.baseline_cmd import cmd_show, cmd_reset, build_parser


@pytest.fixture
def bfile(tmp_path):
    return str(tmp_path / "baseline.json")


@pytest.fixture
def preloaded(bfile):
    store = BaselineStore(bfile)
    for d in [10.0, 12.0, 11.0]:
        store.update("nightly_sync", d)
    store.update("hourly_ping", 2.0)
    return bfile


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"file": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_show_all(preloaded, capsys):
    args = _ns(file=preloaded, job=None)
    cmd_show(args)
    out = capsys.readouterr().out
    assert "nightly_sync" in out
    assert "hourly_ping" in out


def test_cmd_show_single_job(preloaded, capsys):
    args = _ns(file=preloaded, job="nightly_sync")
    cmd_show(args)
    out = capsys.readouterr().out
    assert "nightly_sync" in out
    assert "hourly_ping" not in out


def test_cmd_show_unknown_job(preloaded, capsys):
    args = _ns(file=preloaded, job="ghost")
    cmd_show(args)
    out = capsys.readouterr().out
    assert "No baseline" in out


def test_cmd_show_empty_store(bfile, capsys):
    args = _ns(file=bfile, job=None)
    cmd_show(args)
    out = capsys.readouterr().out
    assert "No baseline data" in out


def test_cmd_reset_existing(preloaded):
    args = _ns(file=preloaded, job="hourly_ping")
    cmd_reset(args)  # should not raise
    store = BaselineStore(preloaded)
    assert store.get("hourly_ping") is None


def test_cmd_reset_nonexistent_exits(preloaded):
    args = _ns(file=preloaded, job="missing")
    with pytest.raises(SystemExit) as exc:
        cmd_reset(args)
    assert exc.value.code == 1


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None


def test_parser_show_subcommand(bfile):
    parser = build_parser()
    args = parser.parse_args(["--file", bfile, "show"])
    assert args.command == "show"
    assert args.func == cmd_show


def test_parser_reset_subcommand(bfile):
    parser = build_parser()
    args = parser.parse_args(["--file", bfile, "reset", "my_job"])
    assert args.command == "reset"
    assert args.job == "my_job"
