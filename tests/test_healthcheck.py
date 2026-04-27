"""Tests for cronwatch.healthcheck."""

import json
import threading
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock
from urllib.request import urlopen
from urllib.error import HTTPError

import pytest

from cronwatch.healthcheck import HealthCheckServer, _build_status, make_handler


def _make_state(failures: int = 0, last_run: datetime = None):
    state = MagicMock()
    state.consecutive_failures = failures
    state.last_run_dt = last_run
    return state


def _tracker_fn(jobs: dict):
    return lambda: jobs


# --- unit tests for _build_status ---

def test_build_status_all_healthy():
    now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    jobs = {"backup": _make_state(0, now)}
    result = _build_status(_tracker_fn(jobs))
    assert result["status"] == "ok"
    assert result["jobs"]["backup"]["healthy"] is True
    assert result["jobs"]["backup"]["last_run"] == now.isoformat()


def test_build_status_degraded_on_failure():
    jobs = {"backup": _make_state(3, None)}
    result = _build_status(_tracker_fn(jobs))
    assert result["status"] == "degraded"
    assert result["jobs"]["backup"]["healthy"] is False
    assert result["jobs"]["backup"]["last_run"] is None


def test_build_status_mixed_jobs():
    jobs = {
        "good": _make_state(0),
        "bad": _make_state(1),
    }
    result = _build_status(_tracker_fn(jobs))
    assert result["status"] == "degraded"


def test_build_status_empty_tracker():
    result = _build_status(_tracker_fn({}))
    assert result["status"] == "ok"
    assert result["jobs"] == {}


# --- integration test with real HTTP server ---

@pytest.fixture()
def healthy_server():
    jobs = {"myjob": _make_state(0)}
    srv = HealthCheckServer("127.0.0.1", 19876, _tracker_fn(jobs))
    srv.start()
    time.sleep(0.05)
    yield srv
    srv.stop()


def test_health_endpoint_returns_200(healthy_server):
    resp = urlopen("http://127.0.0.1:19876/health")
    assert resp.status == 200
    data = json.loads(resp.read())
    assert data["status"] == "ok"


def test_health_root_path(healthy_server):
    resp = urlopen("http://127.0.0.1:19876/")
    assert resp.status == 200


def test_health_unknown_path_returns_404(healthy_server):
    with pytest.raises(HTTPError) as exc_info:
        urlopen("http://127.0.0.1:19876/unknown")
    assert exc_info.value.code == 404


def test_degraded_server_returns_503():
    jobs = {"failing": _make_state(2)}
    srv = HealthCheckServer("127.0.0.1", 19877, _tracker_fn(jobs))
    srv.start()
    time.sleep(0.05)
    try:
        with pytest.raises(HTTPError) as exc_info:
            urlopen("http://127.0.0.1:19877/health")
        assert exc_info.value.code == 503
    finally:
        srv.stop()
