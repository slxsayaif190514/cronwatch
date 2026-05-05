"""CLI commands for inspecting and resetting throttle state."""

from __future__ import annotations

import argparse
import os
import sys

from cronwatch.throttle import ThrottleStore

DEFAULT_PATH = os.environ.get("CRONWATCH_THROTTLE_FILE", "throttle.json")


def _get_store(path: str) -> ThrottleStore:
    return ThrottleStore(path=path)


def cmd_show(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    jobs = [args.job] if args.job else list(store._data.keys())
    if not jobs:
        print("No throttle entries recorded.")
        return
    print(f"{'Job':<30} {'Count':>6}  {'Window Start':<28} {'Last Alert':<28}")
    print("-" * 96)
    for job in sorted(jobs):
        entry = store.get_entry(job)
        if entry is None:
            print(f"{job:<30} {'—':>6}  {'—':<28} {'—':<28}")
        else:
            last = entry.last_alert.isoformat() if entry.last_alert else "—"
            print(f"{job:<30} {entry.count:>6}  {entry.window_start.isoformat():<28} {last:<28}")


def cmd_reset(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    if args.job:
        store.reset(args.job)
        print(f"Throttle reset for job: {args.job}")
    else:
        for job in list(store._data.keys()):
            store.reset(job)
        print("All throttle entries cleared.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch-throttle",
        description="Inspect or reset per-job alert throttle state.",
    )
    parser.add_argument("--file", default=DEFAULT_PATH, help="Path to throttle state file")
    sub = parser.add_subparsers(dest="command", required=True)

    p_show = sub.add_parser("show", help="Show throttle state")
    p_show.add_argument("job", nargs="?", default=None, help="Job name (all if omitted)")
    p_show.set_defaults(func=cmd_show)

    p_reset = sub.add_parser("reset", help="Reset throttle counters")
    p_reset.add_argument("job", nargs="?", default=None, help="Job name (all if omitted)")
    p_reset.set_defaults(func=cmd_reset)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    sys.exit(0)


if __name__ == "__main__":
    main()
