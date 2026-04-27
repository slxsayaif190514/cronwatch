"""Notification channel registry and dispatch for cronwatch alerts."""

from __future__ import annotations

import logging
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)

# Registry: channel_name -> callable(subject, body, config)
_CHANNELS: Dict[str, Callable] = {}


def register_channel(name: str, fn: Callable) -> None:
    """Register a notification channel by name."""
    _CHANNELS[name] = fn
    logger.debug("Registered notification channel: %s", name)


def get_channel(name: str) -> Callable | None:
    """Return a registered channel callable or None."""
    return _CHANNELS.get(name)


def list_channels() -> List[str]:
    """Return sorted list of registered channel names."""
    return sorted(_CHANNELS.keys())


def dispatch(channels: List[str], subject: str, body: str, config: object) -> Dict[str, bool]:
    """Send a notification via each listed channel.

    Returns a dict mapping channel name -> success bool.
    """
    results: Dict[str, bool] = {}
    for name in channels:
        fn = get_channel(name)
        if fn is None:
            logger.warning("Unknown notification channel: %s", name)
            results[name] = False
            continue
        try:
            fn(subject, body, config)
            results[name] = True
            logger.debug("Notification dispatched via %s", name)
        except Exception as exc:  # noqa: BLE001
            logger.error("Channel %s failed: %s", name, exc)
            results[name] = False
    return results


def _noop_channel(subject: str, body: str, config: object) -> None:  # noqa: ARG001
    """A no-op channel useful for testing."""
    pass


# Register built-in no-op channel
register_channel("noop", _noop_channel)
