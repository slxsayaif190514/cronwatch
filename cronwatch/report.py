"""Generate summary reports from job history."""

from datetime import datetime, timedelta
from typing import List, Optional

from cronwatch.history import JobHistory, RunRecord


def _pct(part: int, total: int) -> float:
    return round(100.0 * part / total, 1) if total else 0.0


def job_summary(history: JobHistory, job_name: str, since: Optional[datetime] = None) -> dict:
    """Return a summary dict for a single job over the given time window."""
    records: List[RunRecord] = history.get_records(job_name)
    if since:
        records = [r for r in records if r.started_at >= since]

    total = len(records)
    successes = sum(1 for r in records if r.success)
    failures = total - successes
    avg_dur = history.average_duration(job_name)
    last_ok = history.last_success(job_name)

    return {
        "job_name": job_name,
        "total_runs": total,
        "successes": successes,
        "failures": failures,
        "success_rate_pct": _pct(successes, total),
        "avg_duration_s": avg_dur,
        "last_success_at": last_ok.started_at.isoformat() if last_ok else None,
    }


def all_jobs_report(history: JobHistory, since: Optional[datetime] = None) -> List[dict]:
    """Return summaries for every job that appears in history."""
    job_names = {r.job_name for r in history._records}
    return [job_summary(history, name, since=since) for name in sorted(job_names)]


def format_report(summaries: List[dict]) -> str:
    """Render a list of job summaries as a human-readable text block."""
    if not summaries:
        return "No job history found.\n"

    lines = ["cronwatch — Job Summary Report", "=" * 40]
    for s in summaries:
        lines.append(f"Job: {s['job_name']}")
        lines.append(f"  Runs      : {s['total_runs']} (✓ {s['successes']}  ✗ {s['failures']})")
        lines.append(f"  Success % : {s['success_rate_pct']}%")
        if s["avg_duration_s"] is not None:
            lines.append(f"  Avg dur   : {s['avg_duration_s']:.1f}s")
        if s["last_success_at"]:
            lines.append(f"  Last OK   : {s['last_success_at']}")
        lines.append("")
    return "\n".join(lines)
