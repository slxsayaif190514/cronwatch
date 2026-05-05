"""Tests for cronwatch.labels."""

from __future__ import annotations

import pytest

from cronwatch.labels import (
    filter_jobs,
    get_all_label_keys,
    get_jobs_by_label,
    label_summary,
    parse_label,
)


def _make_job(name: str, labels: dict):
    """Create a minimal JobConfig-like object."""
    from types import SimpleNamespace
    return SimpleNamespace(name=name, labels=labels)


def _make_config(jobs):
    from types import SimpleNamespace
    return SimpleNamespace(jobs=jobs)


# --- parse_label ---

def test_parse_label_valid():
    assert parse_label("env=prod") == ("env", "prod")


def test_parse_label_with_spaces():
    assert parse_label(" team = infra ") == ("team", "infra")


def test_parse_label_no_equals_raises():
    with pytest.raises(ValueError, match="Invalid label format"):
        parse_label("envprod")


def test_parse_label_empty_key_raises():
    with pytest.raises(ValueError, match="must not be empty"):
        parse_label("=value")


# --- get_jobs_by_label ---

@pytest.fixture
def cfg():
    jobs = [
        _make_job("backup", {"env": "prod", "team": "infra"}),
        _make_job("report", {"env": "staging", "team": "data"}),
        _make_job("cleanup", {"env": "prod", "team": "data"}),
        _make_job("nolabels", {}),
    ]
    return _make_config(jobs)


def test_get_jobs_by_label_key_only(cfg):
    jobs = get_jobs_by_label(cfg, "env")
    assert {j.name for j in jobs} == {"backup", "report", "cleanup"}


def test_get_jobs_by_label_key_and_value(cfg):
    jobs = get_jobs_by_label(cfg, "env", "prod")
    assert {j.name for j in jobs} == {"backup", "cleanup"}


def test_get_jobs_by_label_no_match(cfg):
    assert get_jobs_by_label(cfg, "env", "dev") == []


def test_get_all_label_keys_sorted_unique(cfg):
    assert get_all_label_keys(cfg) == ["env", "team"]


def test_get_all_label_keys_empty():
    assert get_all_label_keys(_make_config([])) == []


# --- label_summary ---

def test_label_summary_structure(cfg):
    summary = label_summary(cfg)
    assert summary["env"]["prod"] == ["backup", "cleanup"]
    assert summary["team"]["data"] == ["report", "cleanup"]


# --- filter_jobs ---

def test_filter_jobs_valid_selector(cfg):
    jobs = filter_jobs(cfg, "team=infra")
    assert [j.name for j in jobs] == ["backup"]


def test_filter_jobs_bad_selector_raises(cfg):
    with pytest.raises(ValueError):
        filter_jobs(cfg, "badformat")
