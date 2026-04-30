"""Tag-based filtering for cron jobs.

Allows jobs to be grouped by tags so checks, alerts, and reports
can be scoped to a subset of jobs.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from cronwatch.config import Config, JobConfig


def get_jobs_by_tag(config: Config, tag: str) -> List[JobConfig]:
    """Return all jobs that include *tag* in their tags list."""
    return [job for job in config.jobs if tag in (job.tags or [])]


def get_all_tags(config: Config) -> List[str]:
    """Return a sorted, deduplicated list of every tag used across all jobs."""
    seen: set[str] = set()
    for job in config.jobs:
        for t in job.tags or []:
            seen.add(t)
    return sorted(seen)


def filter_jobs(
    jobs: Iterable[JobConfig],
    include_tags: Optional[List[str]] = None,
    exclude_tags: Optional[List[str]] = None,
) -> List[JobConfig]:
    """Filter *jobs* by include/exclude tag lists.

    - If *include_tags* is given, only jobs that share at least one tag
      with the list are returned.
    - If *exclude_tags* is given, jobs that share any tag with the list
      are dropped.
    - Both filters may be combined.
    """
    result: List[JobConfig] = []
    for job in jobs:
        job_tags: set[str] = set(job.tags or [])

        if include_tags is not None:
            if not job_tags.intersection(include_tags):
                continue

        if exclude_tags is not None:
            if job_tags.intersection(exclude_tags):
                continue

        result.append(job)
    return result


def tag_summary(config: Config) -> Dict[str, List[str]]:
    """Return a mapping of tag -> [job_name, ...] for all tags."""
    mapping: Dict[str, List[str]] = {}
    for job in config.jobs:
        for tag in job.tags or []:
            mapping.setdefault(tag, []).append(job.name)
    return {k: sorted(v) for k, v in sorted(mapping.items())}
