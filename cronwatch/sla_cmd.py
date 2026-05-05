"""CLI commands for querying and managing SLA records."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from cronwatch.sla import SLAStore

DEFAULT_SLA_FILE = "sla.json"


def _get_store(path: str) -> SLAStore:
    return SLAStore(path)


def cmd_show(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    jobs = [args.job] if args.job else _all_jobs(store)
    if not jobs:
        print("No SLA records found.")
        return
    for job in sorted(jobs):
        pct = store.compliance_for(job)
        if pct is None:
            print(f"{job}: no data")
        else:
            records = store.get_records(job)
            total = sum(r.total_runs for r in records)
            on_time = sum(r.on_time_runs for r in records)
            print(f"{job}: {pct}% ({on_time}/{total} on-time across {len(records)} window(s))")


def cmd_clear(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    store.clear(args.job)
    print(f"Cleared SLA records for '{args.job}'.")


def cmd_windows(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    records = store.get_records(args.job)
    if not records:
        print(f"No SLA windows found for '{args.job}'.")
        return
    print(f"SLA windows for '{args.job}':")
    for r in records:
        print(
            f"  {r.window_start.strftime('%Y-%m-%d %H:%M')} -> "
            f"{r.window_end.strftime('%Y-%m-%d %H:%M')}  "
            f"{r.compliance_pct}% ({r.on_time_runs}/{r.total_runs})"
        )


def _all_jobs(store: SLAStore) -> list:
    # pylint: disable=protected-access
    return list(store._records.keys())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cronwatch-sla", description="Manage SLA records")
    parser.add_argument("--file", default=DEFAULT_SLA_FILE, help="Path to SLA store file")
    sub = parser.add_subparsers(dest="command")

    p_show = sub.add_parser("show", help="Show SLA compliance")
    p_show.add_argument("job", nargs="?", default=None, help="Job name (omit for all)")
    p_show.set_defaults(func=cmd_show)

    p_windows = sub.add_parser("windows", help="List SLA windows for a job")
    p_windows.add_argument("job", help="Job name")
    p_windows.set_defaults(func=cmd_windows)

    p_clear = sub.add_parser("clear", help="Clear SLA data for a job")
    p_clear.add_argument("job", help="Job name")
    p_clear.set_defaults(func=cmd_clear)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
