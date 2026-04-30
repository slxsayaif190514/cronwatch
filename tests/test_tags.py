"""Tests for cronwatch.tags tag-filtering helpers."""

from __future__ import annotations

import pytest

from cronwatch.config import AlertConfig, Config, JobConfig
from cronwatch.tags import filter_jobs, get_all_tags, get_jobs_by_tag, tag_summary


def _make_config() -> Config:
    return Config(
        jobs=[
            JobConfig(name="backup", schedule="0 2 * * *", tags=["infra", "nightly"]),
            JobConfig(name="report", schedule="0 8 * * 1", tags=["reports", "weekly"]),
            JobConfig(name="cleanup", schedule="0 3 * * *", tags=["infra"]),
            JobConfig(name="ping", schedule="* * * * *", tags=[]),
        ]
    )


@pytest.fixture
def cfg() -> Config:
    return _make_config()


def test_get_jobs_by_tag_returns_matching(cfg):
    result = get_jobs_by_tag(cfg, "infra")
    assert [j.name for j in result] == ["backup", "cleanup"]


def test_get_jobs_by_tag_no_match(cfg):
    result = get_jobs_by_tag(cfg, "nonexistent")
    assert result == []


def test_get_all_tags_sorted_unique(cfg):
    tags = get_all_tags(cfg)
    assert tags == ["infra", "nightly", "reports", "weekly"]


def test_get_all_tags_no_tags():
    cfg = Config(jobs=[JobConfig(name="x", schedule="* * * * *")])
    assert get_all_tags(cfg) == []


def test_filter_jobs_include_tags(cfg):
    result = filter_jobs(cfg.jobs, include_tags=["nightly"])
    assert [j.name for j in result] == ["backup"]


def test_filter_jobs_exclude_tags(cfg):
    result = filter_jobs(cfg.jobs, exclude_tags=["infra"])
    names = [j.name for j in result]
    assert "backup" not in names
    assert "cleanup" not in names
    assert "report" in names


def test_filter_jobs_include_and_exclude(cfg):
    result = filter_jobs(cfg.jobs, include_tags=["infra"], exclude_tags=["nightly"])
    assert [j.name for j in result] == ["cleanup"]


def test_filter_jobs_no_filters_returns_all(cfg):
    result = filter_jobs(cfg.jobs)
    assert len(result) == len(cfg.jobs)


def test_tag_summary(cfg):
    summary = tag_summary(cfg)
    assert summary["infra"] == ["backup", "cleanup"]
    assert summary["nightly"] == ["backup"]
    assert summary["reports"] == ["report"]
    assert "infra" in summary


def test_tag_summary_empty_config():
    cfg = Config(jobs=[])
    assert tag_summary(cfg) == {}
