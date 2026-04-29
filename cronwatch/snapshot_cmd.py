"""CLI helper: capture a snapshot of current job states and print a summary."""

from __future__ import annotations

import argparse
import sys
from typing import Callable, Optional

from cronwatch.config import load_config
from cronwatch.schedule import is_overdue
from cronwatch.snapshot import JobSnapshot, SnapshotStore
from cronwatch.tracker import JobTracker

try:
    from cronwatch.silence import SilenceStore
except ImportError:  # pragma: no cover
    SilenceStore = None  # type: ignore


def capture_snapshot(
    config_path: str,
    snapshot_path: str,
    tracker_factory: Optional[Callable] = None,
) -> int:
    """Load config, evaluate each job, persist snapshot. Returns exit code."""
    try:
        cfg = load_config(config_path)
    except Exception as exc:  # noqa: BLE001
        print(f"[snapshot] failed to load config: {exc}", file=sys.stderr)
        return 1

    store = SnapshotStore(snapshot_path)
    snapshots = []

    for job in cfg.jobs:
        if tracker_factory:
            tracker = tracker_factory(job.name)
        else:
            tracker = JobTracker(job.name)

        state = tracker.get_state(job.name)
        last_run = state.last_run_dt
        last_status = state.last_status if hasattr(state, "last_status") else None
        failures = getattr(state, "consecutive_failures", 0)

        overdue = is_overdue(job.schedule, last_run, job.grace_minutes)

        silenced = False
        if SilenceStore is not None:
            try:
                ss = SilenceStore(f".silence_{job.name}.json")
                silenced = ss.is_silenced(job.name)
            except Exception:  # noqa: BLE001
                pass

        snapshots.append(
            JobSnapshot(
                job_name=job.name,
                last_run=last_run.isoformat() if last_run else None,
                last_status=last_status,
                consecutive_failures=failures,
                is_overdue=overdue,
                silenced=silenced,
            )
        )

    snap = store.save(snapshots)
    print(f"[snapshot] captured {len(snapshots)} job(s) at {snap.captured_at}")
    for j in snap.jobs:
        flags = []
        if j["is_overdue"]:
            flags.append("OVERDUE")
        if j["silenced"]:
            flags.append("SILENCED")
        flag_str = " " + ",".join(flags) if flags else ""
        print(f"  {j['job_name']}: last_run={j['last_run']} failures={j['consecutive_failures']}{flag_str}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Capture a cronwatch job snapshot")
    parser.add_argument("--config", default="cronwatch/config_example.json")
    parser.add_argument("--output", default="snapshot.json")
    args = parser.parse_args(argv)
    return capture_snapshot(args.config, args.output)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
