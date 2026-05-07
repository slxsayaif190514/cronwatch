"""Tests for cronwatch.cooldown_cmd."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.cooldown import CooldownStore, _fmt
from cronwatch.cooldown_cmd import cmd_reset, cmd_show


@pytest.fixture
def cfile(tmp_path: Path) -> Path:
    return tmp_path / "cooldown.json"


def _ns(cfile: Path, **kwargs) -> argparse.Namespace:
    defaults = dict(store=str(cfile), cooldown=300, job=None)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _past(seconds: int) -> str:
    return _fmt(datetime.now(timezone.utc) - timedelta(seconds=seconds))


def test_cmd_show_empty(cfile: Path, capsys) -> None:
    cmd_show(_ns(cfile))
    out = capsys.readouterr().out
    assert "No cooldown records found" in out


def test_cmd_show_all_jobs(cfile: Path, capsys) -> None:
    cfile.write_text(json.dumps({"job_a": _past(600), "job_b": _past(100)}))
    cmd_show(_ns(cfile, cooldown=300))
    out = capsys.readouterr().out
    assert "job_a" in out
    assert "job_b" in out
    assert "OK" in out
    assert "COOLING" in out


def test_cmd_show_single_job(cfile: Path, capsys) -> None:
    cfile.write_text(json.dumps({"job_a": _past(10), "job_b": _past(10)}))
    cmd_show(_ns(cfile, job="job_a"))
    out = capsys.readouterr().out
    assert "job_a" in out
    assert "job_b" not in out


def test_cmd_reset_single_job(cfile: Path, capsys) -> None:
    cfile.write_text(json.dumps({"job_a": _past(10), "job_b": _past(10)}))
    cmd_reset(_ns(cfile, job="job_a"))
    store = CooldownStore(str(cfile))
    assert store.last_alert("job_a") is None
    assert store.last_alert("job_b") is not None
    out = capsys.readouterr().out
    assert "job_a" in out


def test_cmd_reset_all_jobs(cfile: Path, capsys) -> None:
    cfile.write_text(json.dumps({"job_a": _past(10), "job_b": _past(10)}))
    cmd_reset(_ns(cfile, job=None))
    store = CooldownStore(str(cfile))
    assert store.all_jobs() == []
    out = capsys.readouterr().out
    assert "cleared" in out
