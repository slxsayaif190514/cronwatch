"""Tests for cronwatch.jitter and cronwatch.jitter_cmd."""
from __future__ import annotations

import argparse
import os
import pytest

from cronwatch.jitter import JitterStore
from cronwatch.jitter_cmd import cmd_show, cmd_reset, build_parser


@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "jitter.json")


@pytest.fixture
def store(store_file):
    return JitterStore(store_file)


def test_empty_store_returns_no_jobs(store):
    assert store.all_jobs() == []


def test_record_persists_sample(store, store_file):
    store.record("backup", 15.0)
    reloaded = JitterStore(store_file)
    assert reloaded.get_samples("backup") == [15.0]


def test_avg_jitter_uses_absolute_values(store):
    store.record("job", -30.0)
    store.record("job", 10.0)
    avg = store.avg_jitter("job")
    assert avg == pytest.approx(20.0)


def test_avg_jitter_unknown_job_returns_none(store):
    assert store.avg_jitter("ghost") is None


def test_is_high_jitter_below_threshold(store):
    store.record("job", 5.0)
    assert not store.is_high_jitter("job", threshold_s=60.0)


def test_is_high_jitter_above_threshold(store):
    store.record("job", 120.0)
    assert store.is_high_jitter("job", threshold_s=60.0)


def test_max_samples_truncates_oldest(store):
    for i in range(5):
        store.record("job", float(i), max_samples=3)
    assert store.get_samples("job") == [2.0, 3.0, 4.0]


def test_reset_clears_job(store):
    store.record("job", 10.0)
    store.reset("job")
    assert store.get_samples("job") == []
    assert "job" not in store.all_jobs()


def _ns(file, **kw):
    return argparse.Namespace(file=file, **kw)


def test_cmd_show_empty(store_file, capsys):
    cmd_show(_ns(store_file, job=None, threshold=60.0))
    out = capsys.readouterr().out
    assert "No jitter data" in out


def test_cmd_show_with_data(store_file, capsys):
    s = JitterStore(store_file)
    s.record("daily", 90.0)
    cmd_show(_ns(store_file, job="daily", threshold=60.0))
    out = capsys.readouterr().out
    assert "daily" in out
    assert "HIGH" in out


def test_cmd_reset_single(store_file, capsys):
    s = JitterStore(store_file)
    s.record("daily", 5.0)
    cmd_reset(_ns(store_file, job="daily"))
    assert JitterStore(store_file).get_samples("daily") == []


def test_build_parser_returns_parser():
    p = build_parser()
    args = p.parse_args(["show"])
    assert args.command == "show"
