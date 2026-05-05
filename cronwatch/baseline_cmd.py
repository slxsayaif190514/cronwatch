"""CLI commands for inspecting and managing baseline duration stats."""

from __future__ import annotations

import argparse
import os
import sys

from cronwatch.baseline import BaselineStore

_DEFAULT_PATH = os.environ.get("CRONWATCH_BASELINE_FILE", "baseline.json")


def _get_store(path: str) -> BaselineStore:
    return BaselineStore(path)


def cmd_show(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    stats = store.all_stats()
    if not stats:
        print("No baseline data recorded yet.")
        return
    if args.job:
        stats = [s for s in stats if s.job_name == args.job]
        if not stats:
            print(f"No baseline for job '{args.job}'.")
            return
    print(f"{'Job':<30} {'Samples':>8} {'Avg (s)':>10} {'Stddev (s)':>12} {'Upper 2σ (s)':>14}")
    print("-" * 78)
    for s in sorted(stats, key=lambda x: x.job_name):
        print(
            f"{s.job_name:<30} {s.sample_count:>8} "
            f"{s.avg_duration_s:>10.2f} {s.stddev_s:>12.2f} "
            f"{s.upper_bound():>14.2f}"
        )


def cmd_reset(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    if store.reset(args.job):
        print(f"Baseline for '{args.job}' cleared.")
    else:
        print(f"No baseline found for '{args.job}'.")
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch-baseline",
        description="Manage cronwatch baseline duration statistics.",
    )
    parser.add_argument("--file", default=_DEFAULT_PATH, help="Path to baseline JSON file")
    sub = parser.add_subparsers(dest="command", required=True)

    show_p = sub.add_parser("show", help="Show baseline stats")
    show_p.add_argument("--job", default=None, help="Filter to a single job")
    show_p.set_defaults(func=cmd_show)

    reset_p = sub.add_parser("reset", help="Clear baseline for a job")
    reset_p.add_argument("job", help="Job name to reset")
    reset_p.set_defaults(func=cmd_reset)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
