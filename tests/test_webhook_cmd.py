"""Tests for webhook_cmd CLI."""

import json
import pytest

from cronwatch.webhook_cmd import build_parser, cmd_add, cmd_list, cmd_remove, cmd_show


@pytest.fixture
def reg_path(tmp_path):
    return str(tmp_path / "wh.json")


def _ns(reg_path, **kw):
    """Build a minimal namespace mimicking parsed args."""
    import argparse
    defaults = dict(registry=reg_path, name=None, url=None, secret=None, timeout=10, disabled=False)
    defaults.update(kw)
    return argparse.Namespace(**defaults)


def test_cmd_add_creates_endpoint(reg_path):
    args = _ns(reg_path, name="pagerduty", url="https://pd.example.com")
    rc = cmd_add(args)
    assert rc == 0
    data = json.loads(open(reg_path).read())
    assert data["webhooks"][0]["name"] == "pagerduty"


def test_cmd_add_disabled_flag(reg_path):
    args = _ns(reg_path, name="off", url="https://off.example.com", disabled=True)
    cmd_add(args)
    data = json.loads(open(reg_path).read())
    assert data["webhooks"][0]["enabled"] is False


def test_cmd_remove_existing(reg_path):
    add_args = _ns(reg_path, name="to_del", url="https://del.example.com")
    cmd_add(add_args)
    rm_args = _ns(reg_path, name="to_del")
    rc = cmd_remove(rm_args)
    assert rc == 0


def test_cmd_remove_missing_returns_one(reg_path):
    args = _ns(reg_path, name="ghost")
    rc = cmd_remove(args)
    assert rc == 1


def test_cmd_list_empty(reg_path, capsys):
    args = _ns(reg_path)
    rc = cmd_list(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "No webhooks" in captured.out


def test_cmd_list_shows_entries(reg_path, capsys):
    cmd_add(_ns(reg_path, name="slack", url="https://slack.example.com"))
    rc = cmd_list(_ns(reg_path))
    assert rc == 0
    out = capsys.readouterr().out
    assert "slack" in out


def test_cmd_show_existing(reg_path, capsys):
    cmd_add(_ns(reg_path, name="show_me", url="https://show.example.com"))
    rc = cmd_show(_ns(reg_path, name="show_me"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "show_me" in out


def test_cmd_show_missing_returns_one(reg_path):
    rc = cmd_show(_ns(reg_path, name="nope"))
    assert rc == 1


def test_build_parser_no_command_returns_parser():
    p = build_parser()
    args = p.parse_args(["list"])
    assert args.command == "list"
