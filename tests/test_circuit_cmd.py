"""Tests for cronwatch.circuit_cmd."""

from __future__ import annotations

import argparse
import pytest
from pathlib import Path
from cronwatch.circuit import CircuitStore
from cronwatch.circuit_cmd import cmd_show, cmd_reset, build_parser


@pytest.fixture
def cfile(tmp_path: Path) -> Path:
    return tmp_path / "circuit.json"


def _ns(cfile: Path, **kwargs) -> argparse.Namespace:
    defaults = dict(file=str(cfile), threshold=3, reset_after=600)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_show_empty(cfile: Path, capsys):
    cmd_show(_ns(cfile, job=None))
    out = capsys.readouterr().out
    assert "No circuit breaker" in out


def test_cmd_show_all_jobs(cfile: Path, capsys):
    s = CircuitStore(str(cfile), threshold=3)
    s.record_failure("job_a")
    cmd_show(_ns(cfile, job=None))
    out = capsys.readouterr().out
    assert "job_a" in out
    assert "failures=1" in out


def test_cmd_show_single_job(cfile: Path, capsys):
    s = CircuitStore(str(cfile), threshold=3)
    s.record_failure("job_b")
    s.record_failure("job_b")
    cmd_show(_ns(cfile, job="job_b"))
    out = capsys.readouterr().out
    assert "job_b" in out
    assert "failures=2" in out


def test_cmd_show_open_status(cfile: Path, capsys):
    s = CircuitStore(str(cfile), threshold=2)
    s.record_failure("job_c")
    s.record_failure("job_c")
    cmd_show(_ns(cfile, job="job_c", threshold=2))
    out = capsys.readouterr().out
    assert "OPEN" in out


def test_cmd_reset_clears_entry(cfile: Path, capsys):
    s = CircuitStore(str(cfile), threshold=3)
    s.record_failure("job_d")
    cmd_reset(_ns(cfile, job="job_d"))
    out = capsys.readouterr().out
    assert "reset" in out.lower()
    s2 = CircuitStore(str(cfile), threshold=3)
    assert s2.get("job_d").failures == 0


def test_build_parser_returns_parser():
    p = build_parser()
    assert p is not None
    args = p.parse_args(["show"])
    assert args.cmd == "show"
