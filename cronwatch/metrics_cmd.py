"""CLI commands for viewing job metrics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwatch.metrics import MetricsStore

_DEFAULT_PATH = Path("metrics.json")


def _get_store(path: str) -> MetricsStore:
    return MetricsStore(Path(path))


def cmd_show(ns: argparse.Namespace) -> None:
    store = _get_store(ns.metrics_file)
    if ns.job:
        metrics = [store.get(ns.job)]
    else:
        metrics = store.all_metrics()

    if not metrics:
        print("No metrics recorded.")
        return

    for m in metrics:
        avg = f"{m.avg_duration_s:.2f}s" if m.avg_duration_s is not None else "n/a"
        mn = f"{m.min_duration_s:.2f}s" if m.min_duration_s is not None else "n/a"
        mx = f"{m.max_duration_s:.2f}s" if m.max_duration_s is not None else "n/a"
        print(f"[{m.job_name}]")
        print(f"  runs:    {m.total_runs} (ok={m.success_runs}, fail={m.failure_runs})")
        print(f"  duration avg={avg} min={mn} max={mx}")


def cmd_reset(ns: argparse.Namespace) -> None:
    store = _get_store(ns.metrics_file)
    store.reset(ns.job)
    print(f"Metrics reset for job '{ns.job}'.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwatch-metrics", description="Inspect job run metrics")
    p.add_argument("--metrics-file", default=str(_DEFAULT_PATH), metavar="FILE")
    sub = p.add_subparsers(dest="command", required=True)

    sh = sub.add_parser("show", help="Show metrics")
    sh.add_argument("--job", default=None, help="Filter to a single job")
    sh.set_defaults(func=cmd_show)

    rs = sub.add_parser("reset", help="Reset metrics for a job")
    rs.add_argument("job", help="Job name to reset")
    rs.set_defaults(func=cmd_reset)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    ns.func(ns)
    return 0


if __name__ == "__main__":
    sys.exit(main())
