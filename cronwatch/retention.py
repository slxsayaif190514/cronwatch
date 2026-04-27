"""Prune old history and digest records based on configurable retention policy."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from cronwatch.history import HistoryStore
from cronwatch.digest import DigestStore

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def prune_history(store: HistoryStore, max_age_days: int, job_name: Optional[str] = None) -> int:
    """Remove run records older than *max_age_days*.

    If *job_name* is given only that job's records are pruned.
    Returns the number of records removed.
    """
    if max_age_days <= 0:
        raise ValueError("max_age_days must be a positive integer")

    cutoff = _utcnow() - timedelta(days=max_age_days)
    records = store.get_records(job_name) if job_name else store.get_records()
    removed = 0

    for record in records:
        if record.started_at < cutoff:
            store.delete_record(record.id)
            removed += 1

    if removed:
        logger.info(
            "pruned %d history record(s) older than %d day(s)%s",
            removed,
            max_age_days,
            f" for job '{job_name}'" if job_name else "",
        )
    return removed


def prune_digest(store: DigestStore, max_age_days: int) -> int:
    """Remove digest events older than *max_age_days*.

    Returns the number of events removed.
    """
    if max_age_days <= 0:
        raise ValueError("max_age_days must be a positive integer")

    cutoff = _utcnow() - timedelta(days=max_age_days)
    events = store.get_events()
    kept = [e for e in events if e["timestamp"] >= cutoff.isoformat()]
    removed = len(events) - len(kept)

    if removed:
        store.clear()
        for event in kept:
            store.add_event(event)
        logger.info("pruned %d digest event(s) older than %d day(s)", removed, max_age_days)

    return removed


def run_retention(history: HistoryStore, digest: DigestStore, max_age_days: int) -> dict:
    """Run full retention pass over history and digest stores.

    Returns a summary dict with counts of pruned records.
    """
    history_pruned = prune_history(history, max_age_days)
    digest_pruned = prune_digest(digest, max_age_days)
    return {"history_pruned": history_pruned, "digest_pruned": digest_pruned}
