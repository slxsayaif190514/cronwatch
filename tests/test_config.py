import json
import os
import tempfile
import pytest
from cronwatch.config import load_config, Config, JobConfig, AlertConfig


SAMPLE_CONFIG = {
    "check_interval_seconds": 30,
    "state_file": "/tmp/state.json",
    "log_file": "/tmp/cronwatch.log",
    "alerts": {
        "email": "test@example.com",
        "webhook_url": "https://example.com/hook"
    },
    "jobs": [
        {
            "name": "test-job",
            "schedule": "* * * * *",
            "max_delay_seconds": 120,
            "alert_on_failure": True,
            "alert_on_delay": False,
            "tags": ["test"]
        }
    ]
}


@pytest.fixture
def config_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(SAMPLE_CONFIG, f)
        path = f.name
    yield path
    os.unlink(path)


def test_load_config_returns_config_object(config_file):
    cfg = load_config(config_file)
    assert isinstance(cfg, Config)


def test_load_config_jobs(config_file):
    cfg = load_config(config_file)
    assert len(cfg.jobs) == 1
    job = cfg.jobs[0]
    assert isinstance(job, JobConfig)
    assert job.name == "test-job"
    assert job.schedule == "* * * * *"
    assert job.max_delay_seconds == 120
    assert job.alert_on_failure is True
    assert job.alert_on_delay is False
    assert job.tags == ["test"]


def test_load_config_alerts(config_file):
    cfg = load_config(config_file)
    assert isinstance(cfg.alerts, AlertConfig)
    assert cfg.alerts.email == "test@example.com"
    assert cfg.alerts.webhook_url == "https://example.com/hook"
    assert cfg.alerts.slack_channel is None


def test_load_config_top_level(config_file):
    cfg = load_config(config_file)
    assert cfg.check_interval_seconds == 30
    assert cfg.state_file == "/tmp/state.json"


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/config.json")


def test_load_config_defaults():
    minimal = {"jobs": [{"name": "j", "schedule": "* * * * *"}]}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(minimal, f)
        path = f.name
    try:
        cfg = load_config(path)
        assert cfg.jobs[0].max_delay_seconds == 300
        assert cfg.jobs[0].alert_on_failure is True
    finally:
        os.unlink(path)
