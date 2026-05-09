"""CLI commands for inspecting burst detection state."""

from __future__ import annotations

import argparse
import sys

from cronwatch.burst import BurstStore

_DEFAULT_PATH = "burst.json"
_DEFAULT_WINDOW = 3600
_DEFAULT_MAX = 10


def _get_store(path: str) -> BurstStore:
    return BurstStore(path)


def cmd_show(ns: argparse.Namespace) -> None:
    store = _get_store(ns.file)
    jobs = [ns.job] if ns.job else store.all_jobs()
    if not jobs:
        print("No burst data recorded.")
        return
    print(f"{'JOB':<30} {'RUNS (window)':<15} {'BURSTING?':<10}")
    print("-" * 58)
    for job in jobs:
        count = store.get_count(job, ns.window)
        bursting = store.is_bursting(job, ns.max_runs, ns.window)
        flag = "YES" if bursting else "no"
        print(f"{job:<30} {count:<15} {flag:<10}")


def cmd_reset(ns: argparse.Namespace) -> None:
    store = _get_store(ns.file)
    if ns.job:
        store.reset(ns.job)
        print(f"Burst data cleared for '{ns.job}'.")
    else:
        for job in store.all_jobs():
            store.reset(job)
        print("All burst data cleared.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwatch-burst", description="Burst detection inspector")
    p.add_argument("--file", default=_DEFAULT_PATH, help="Burst store file")
    p.add_argument("--window", type=int, default=_DEFAULT_WINDOW, help="Window in seconds")
    p.add_argument("--max-runs", type=int, default=_DEFAULT_MAX, dest="max_runs",
                   help="Max allowed runs before flagged as burst")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("show", help="Show burst counts")
    s.add_argument("job", nargs="?", default=None)

    r = sub.add_parser("reset", help="Reset burst data")
    r.add_argument("job", nargs="?", default=None)

    return p


def main(argv=None) -> int:
    p = build_parser()
    ns = p.parse_args(argv)
    if ns.cmd == "show":
        cmd_show(ns)
    elif ns.cmd == "reset":
        cmd_reset(ns)
    else:
        p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
