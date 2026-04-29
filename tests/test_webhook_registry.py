"""Tests for WebhookRegistry."""

import json
import os
import pytest

from cronwatch.webhook_registry import WebhookEndpoint, WebhookRegistry


@pytest.fixture
def reg_file(tmp_path):
    return str(tmp_path / "webhooks.json")


@pytest.fixture
def registry(reg_file):
    return WebhookRegistry(reg_file)


def _ep(name="test", url="https://example.com/hook", **kw):
    return WebhookEndpoint(name=name, url=url, **kw)


def test_empty_registry_returns_no_endpoints(registry):
    assert registry.all() == []


def test_register_persists_to_disk(registry, reg_file):
    registry.register(_ep())
    data = json.loads(open(reg_file).read())
    assert len(data["webhooks"]) == 1
    assert data["webhooks"][0]["name"] == "test"


def test_get_returns_registered_endpoint(registry):
    ep = _ep(name="slack", url="https://hooks.slack.com/x")
    registry.register(ep)
    result = registry.get("slack")
    assert result is not None
    assert result.url == "https://hooks.slack.com/x"


def test_get_unknown_returns_none(registry):
    assert registry.get("missing") is None


def test_remove_existing_endpoint(registry):
    registry.register(_ep(name="to_remove"))
    removed = registry.remove("to_remove")
    assert removed is True
    assert registry.get("to_remove") is None


def test_remove_nonexistent_returns_false(registry):
    assert registry.remove("ghost") is False


def test_list_enabled_excludes_disabled(registry):
    registry.register(_ep(name="on", enabled=True))
    registry.register(_ep(name="off", url="https://x.com", enabled=False))
    enabled = registry.list_enabled()
    assert len(enabled) == 1
    assert enabled[0].name == "on"


def test_registry_loads_from_existing_file(reg_file):
    data = {"webhooks": [{"name": "pre", "url": "https://pre.example.com", "enabled": True}]}
    with open(reg_file, "w") as f:
        json.dump(data, f)
    reg = WebhookRegistry(reg_file)
    ep = reg.get("pre")
    assert ep is not None
    assert ep.url == "https://pre.example.com"


def test_endpoint_to_dict_roundtrip():
    ep = WebhookEndpoint(name="x", url="https://x.io", secret="s3cr3t", timeout=5)
    restored = WebhookEndpoint.from_dict(ep.to_dict())
    assert restored == ep
