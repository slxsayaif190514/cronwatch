"""Tests for cronwatch.sla and cronwatch.sla_cmd."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.sla import SLARecord, SLAStore
from cronwatch.sla_cmd import build_parser, cmd_show, cmd_clear, cmd_windows


def _utc(year, month, day, hour=0, minute=0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


@pytest.fixture()
def store_file(tmp_path):
    return str(tmp_path / "sla.json")


@pytest.fixture()
def store(store_file):
    return SLAStore(store_file)


def test_empty_store_returns_no_records(store):
    assert store.get_records("backup") == []


def test_compliance_for_unknown_job_returns_none(store):
    assert store.compliance_for("missing") is None


def test_record_on_time_run_increments(store):
    ws = _utc(2024, 1, 1, 6)
    we = _utc(2024, 1, 1, 7)
    store.record_run("backup", ws, we, on_time=True)
    recs = store.get_records("backup")
    assert len(recs) == 1
    assert recs[0].total_runs == 1
    assert recs[0].on_time_runs == 1


def test_record_late_run_does_not_increment_on_time(store):
    ws = _utc(2024, 1, 1, 6)
    we = _utc(2024, 1, 1, 7)
    store.record_run("backup", ws, we, on_time=False)
    recs = store.get_records("backup")
    assert recs[0].on_time_runs == 0
    assert recs[0].total_runs == 1


def test_compliance_pct_calculation(store):
    ws = _utc(2024, 1, 1, 6)
    we = _utc(2024, 1, 1, 7)
    store.record_run("backup", ws, we, on_time=True)
    store.record_run("backup", ws, we, on_time=False)
    assert store.compliance_for("backup") == 50.0


def test_record_persists_to_disk(store_file):
    ws = _utc(2024, 2, 1)
    we = _utc(2024, 2, 1, 1)
    s1 = SLAStore(store_file)
    s1.record_run("etl", ws, we, on_time=True)
    s2 = SLAStore(store_file)
    assert s2.compliance_for("etl") == 100.0


def test_clear_removes_job(store):
    ws = _utc(2024, 3, 1)
    we = _utc(2024, 3, 1, 1)
    store.record_run("etl", ws, we, on_time=True)
    store.clear("etl")
    assert store.get_records("etl") == []


def test_sla_record_100pct_when_no_runs():
    r = SLARecord("job", _utc(2024, 1, 1), _utc(2024, 1, 2))
    assert r.compliance_pct == 100.0


def test_cmd_show_no_data(store_file, capsys):
    ns = build_parser().parse_args(["--file", store_file, "show"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "No SLA records" in out


def test_cmd_show_single_job(store_file, capsys):
    s = SLAStore(store_file)
    s.record_run("backup", _utc(2024, 1, 1), _utc(2024, 1, 1, 1), on_time=True)
    ns = build_parser().parse_args(["--file", store_file, "show", "backup"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "backup" in out
    assert "100.0%" in out


def test_cmd_windows_lists_entries(store_file, capsys):
    s = SLAStore(store_file)
    s.record_run("etl", _utc(2024, 5, 1), _utc(2024, 5, 1, 1), on_time=False)
    ns = build_parser().parse_args(["--file", store_file, "windows", "etl"])
    ns.func(ns)
    out = capsys.readouterr().out
    assert "etl" in out
    assert "0.0%" in out
