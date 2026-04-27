"""Tests for cronwatch.notifier channel registry and dispatch."""

from __future__ import annotations

import pytest
from cronwatch import notifier


@pytest.fixture(autouse=True)
def _clean_registry():
    """Restore original registry state after each test."""
    original = dict(notifier._CHANNELS)
    yield
    notifier._CHANNELS.clear()
    notifier._CHANNELS.update(original)


def test_register_and_get_channel():
    fn = lambda s, b, c: None  # noqa: E731
    notifier.register_channel("test_chan", fn)
    assert notifier.get_channel("test_chan") is fn


def test_get_unknown_channel_returns_none():
    assert notifier.get_channel("does_not_exist") is None


def test_list_channels_includes_noop():
    assert "noop" in notifier.list_channels()


def test_list_channels_sorted():
    notifier.register_channel("zzz", lambda s, b, c: None)
    notifier.register_channel("aaa", lambda s, b, c: None)
    names = notifier.list_channels()
    assert names == sorted(names)


def test_dispatch_success():
    calls = []
    notifier.register_channel("cap", lambda s, b, c: calls.append((s, b)))
    results = notifier.dispatch(["cap"], "subj", "body", object())
    assert results == {"cap": True}
    assert calls == [("subj", "body")]


def test_dispatch_unknown_channel_returns_false():
    results = notifier.dispatch(["ghost"], "s", "b", object())
    assert results == {"ghost": False}


def test_dispatch_channel_exception_returns_false():
    def boom(s, b, c):
        raise RuntimeError("oops")

    notifier.register_channel("boom", boom)
    results = notifier.dispatch(["boom"], "s", "b", object())
    assert results == {"boom": False}


def test_dispatch_noop_succeeds():
    results = notifier.dispatch(["noop"], "hi", "there", None)
    assert results == {"noop": True}


def test_dispatch_multiple_channels():
    notifier.register_channel("a", lambda s, b, c: None)
    notifier.register_channel("b", lambda s, b, c: None)
    results = notifier.dispatch(["a", "b", "missing"], "s", "b", None)
    assert results["a"] is True
    assert results["b"] is True
    assert results["missing"] is False
