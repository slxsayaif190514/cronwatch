"""Tests for the cronwatch CLI entry point."""

import json
import os
import pytest
from unittest.mock import MagicMock, patch

from cronwatch.cli import parse_args, main


@pytest.fixture
def config_file(tmp_path):
    cfg = {
        "jobs": [
            {
                "name": "test_job",
                "schedule": "* * * * *",
                "grace_period_seconds": 60,
            }
        ],
        "alerts": {
            "cooldown_seconds": 300,
            "email": None,
            "webhook_url": None,
        },
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    return str(p)


def test_parse_args_defaults():
    args = parse_args([])
    assert args.interval == 60
    assert args.verbose is False
    assert args.once is False


def test_parse_args_custom(config_file):
    args = parse_args(["-c", config_file, "-i", "30", "-v", "--once"])
    assert args.config == config_file
    assert args.interval == 30
    assert args.verbose is True
    assert args.once is True


def test_main_once_returns_zero(config_file):
    with patch("cronwatch.cli.run_checks") as mock_run:
        result = main(["-c", config_file, "--once"])
    assert result == 0
    mock_run.assert_called_once()


def test_main_bad_config_returns_one(tmp_path):
    missing = str(tmp_path / "nonexistent.json")
    result = main(["-c", missing, "--once"])
    assert result == 1


def test_main_invalid_json_returns_one(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    result = main(["-c", str(bad), "--once"])
    assert result == 1


def test_main_calls_run_checks_with_config_and_tracker(config_file):
    with patch("cronwatch.cli.run_checks") as mock_run:
        main(["-c", config_file, "--once"])
    args_called, kwargs_called = mock_run.call_args
    config_arg, tracker_arg = args_called
    assert hasattr(config_arg, "jobs")
    assert hasattr(tracker_arg, "get_state")
