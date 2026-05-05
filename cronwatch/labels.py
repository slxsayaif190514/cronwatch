"""Key/value label management for cron jobs.

Labels are arbitrary metadata attached to jobs (e.g. team=infra, env=prod).
They complement tags (which are simple strings) by supporting key=value pairs.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from cronwatch.config import Config, JobConfig


def parse_label(raw: str) -> tuple[str, str]:
    """Parse a 'key=value' string into a (key, value) tuple."""
    if "=" not in raw:
        raise ValueError(f"Invalid label format {raw!r}: expected 'key=value'")
    key, _, value = raw.partition("=")
    key = key.strip()
    value = value.strip()
    if not key:
        raise ValueError(f"Label key must not be empty in {raw!r}")
    return key, value


def get_jobs_by_label(config: Config, key: str, value: Optional[str] = None) -> List[JobConfig]:
    """Return jobs that have the given label key, optionally filtered by value."""
    results = []
    for job in config.jobs:
        labels: Dict[str, str] = getattr(job, "labels", {}) or {}
        if key in labels:
            if value is None or labels[key] == value:
                results.append(job)
    return results


def get_all_label_keys(config: Config) -> List[str]:
    """Return a sorted list of unique label keys across all jobs."""
    keys: set[str] = set()
    for job in config.jobs:
        labels: Dict[str, str] = getattr(job, "labels", {}) or {}
        keys.update(labels.keys())
    return sorted(keys)


def label_summary(config: Config) -> Dict[str, Dict[str, List[str]]]:
    """Return a nested dict: {key: {value: [job_names]}}."""
    summary: Dict[str, Dict[str, List[str]]] = {}
    for job in config.jobs:
        labels: Dict[str, str] = getattr(job, "labels", {}) or {}
        for k, v in labels.items():
            summary.setdefault(k, {}).setdefault(v, []).append(job.name)
    return summary


def filter_jobs(config: Config, label_selector: str) -> List[JobConfig]:
    """Filter jobs using a 'key=value' selector string."""
    key, value = parse_label(label_selector)
    return get_jobs_by_label(config, key, value)
