"""CLI commands for inspecting and resetting backoff state."""

import argparse
import sys
from cronwatch.backoff import BackoffStore

_DEFAULT_FILE = "backoff.json"


def _get_store(path: str) -> BackoffStore:
    return BackoffStore(path)


def cmd_show(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    jobs = [args.job] if args.job else list(store._data.keys())
    if not jobs:
        print("No backoff state recorded.")
        return
    fmt = "{:<30} {:>8} {:>12} {}"
    print(fmt.format("JOB", "ATTEMPT", "INTERVAL(s)", "LAST_ALERT"))
    print("-" * 70)
    for job in sorted(jobs):
        entry = store.get(job)
        interval = store.interval_s(job)
        last = entry.last_alert.strftime("%Y-%m-%dT%H:%M:%SZ") if entry.last_alert else "never"
        print(fmt.format(job, entry.attempt, interval, last))


def cmd_reset(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    if args.job:
        store.reset(args.job)
        print(f"Reset backoff for job: {args.job}")
    else:
        for job in list(store._data.keys()):
            store.reset(job)
        print("Reset all backoff state.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwatch-backoff", description="Manage alert backoff state")
    p.add_argument("--file", default=_DEFAULT_FILE, help="Backoff state file")
    sub = p.add_subparsers(dest="cmd", required=True)

    sh = sub.add_parser("show", help="Show backoff state")
    sh.add_argument("job", nargs="?", default=None, help="Filter to a single job")
    sh.set_defaults(func=cmd_show)

    rs = sub.add_parser("reset", help="Reset backoff state")
    rs.add_argument("job", nargs="?", default=None, help="Job to reset (omit for all)")
    rs.set_defaults(func=cmd_reset)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
