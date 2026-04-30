"""Tests for cronwatch.dependency and cronwatch.dependency_cmd."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.dependency import DependencyStore
from cronwatch.dependency_cmd import build_parser


@pytest.fixture()
def dep_file(tmp_path: Path) -> str:
    return str(tmp_path / "deps.json")


@pytest.fixture()
def store(dep_file: str) -> DependencyStore:
    return DependencyStore(dep_file)


def test_get_unknown_job_returns_none(store: DependencyStore) -> None:
    assert store.get("missing") is None


def test_set_dependencies_persists(dep_file: str) -> None:
    store = DependencyStore(dep_file)
    store.set_dependencies("jobB", ["jobA"])
    store2 = DependencyStore(dep_file)
    state = store2.get("jobB")
    assert state is not None
    assert state.depends_on == ["jobA"]


def test_mark_satisfied_sets_timestamp(store: DependencyStore) -> None:
    store.set_dependencies("jobA", [])
    before = datetime.now(timezone.utc)
    store.mark_satisfied("jobA")
    state = store.get("jobA")
    assert state is not None
    assert state.last_satisfied is not None
    assert state.last_satisfied >= before


def test_dependencies_met_no_deps(store: DependencyStore) -> None:
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    assert store.dependencies_met("standalone", since) is True


def test_dependencies_met_satisfied_after_since(store: DependencyStore) -> None:
    store.set_dependencies("jobA", [])
    store.mark_satisfied("jobA")
    store.set_dependencies("jobB", ["jobA"])
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    assert store.dependencies_met("jobB", since) is True


def test_dependencies_not_met_satisfied_before_since(store: DependencyStore) -> None:
    store.set_dependencies("jobA", [])
    store.mark_satisfied("jobA")
    store.set_dependencies("jobB", ["jobA"])
    # since is in the future relative to last_satisfied
    since = datetime.now(timezone.utc) + timedelta(seconds=5)
    assert store.dependencies_met("jobB", since) is False


def test_dependencies_not_met_dep_never_ran(store: DependencyStore) -> None:
    store.set_dependencies("jobB", ["jobA"])
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    assert store.dependencies_met("jobB", since) is False


# --- CLI tests ---

def _ns(dep_file: str, **kwargs):
    defaults = {"deps_file": dep_file}
    defaults.update(kwargs)
    return type("NS", (), defaults)()


def test_cmd_set_creates_entry(dep_file: str) -> None:
    from cronwatch.dependency_cmd import cmd_set
    ns = _ns(dep_file, job="jobB", depends_on=["jobA", "jobC"])
    rc = cmd_set(ns)
    assert rc == 0
    store = DependencyStore(dep_file)
    assert store.get("jobB").depends_on == ["jobA", "jobC"]


def test_cmd_remove_clears_deps(dep_file: str) -> None:
    from cronwatch.dependency_cmd import cmd_remove, cmd_set
    cmd_set(_ns(dep_file, job="jobB", depends_on=["jobA"]))
    rc = cmd_remove(_ns(dep_file, job="jobB"))
    assert rc == 0
    assert DependencyStore(dep_file).get("jobB").depends_on == []


def test_cmd_show_missing_returns_one(dep_file: str) -> None:
    from cronwatch.dependency_cmd import cmd_show
    rc = cmd_show(_ns(dep_file, job="ghost"))
    assert rc == 1
