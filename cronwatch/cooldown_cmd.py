"""CLI sub-commands for inspecting and managing alert cooldown state."""

from __future__ import annotations

import argparse
import sys
from datetime import timezone

from cronwatch.cooldown import CooldownStore

_DEFAULT_STORE = "cooldown.json"


def _get_store(args: argparse.Namespace) -> CooldownStore:
    return CooldownStore(args.store)


def cmd_show(args: argparse.Namespace) -> None:
    store = _get_store(args)
    jobs = [args.job] if args.job else store.all_jobs()
    if not jobs:
        print("No cooldown records found.")
        return
    for job in jobs:
        last = store.last_alert(job)
        ts = last.strftime("%Y-%m-%d %H:%M:%S UTC") if last else "never"
        status = "OK" if store.is_cooled_down(job, args.cooldown) else "COOLING"
        print(f"{job:<30}  last_alert={ts:<24}  status={status}")


def cmd_reset(args: argparse.Namespace) -> None:
    store = _get_store(args)
    if args.job:
        store.reset(args.job)
        print(f"Cooldown reset for job: {args.job}")
    else:
        for job in store.all_jobs():
            store.reset(job)
        print("All cooldown records cleared.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-cooldown",
        description="Inspect and manage per-job alert cooldown state.",
    )
    p.add_argument("--store", default=_DEFAULT_STORE, help="Path to cooldown JSON store")
    p.add_argument("--cooldown", type=int, default=300, help="Cooldown window in seconds (default 300)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sh = sub.add_parser("show", help="Show cooldown state")
    sh.add_argument("job", nargs="?", default=None, help="Specific job name")
    sh.set_defaults(func=cmd_show)

    rs = sub.add_parser("reset", help="Reset cooldown for a job (or all jobs)")
    rs.add_argument("job", nargs="?", default=None, help="Job name (omit for all)")
    rs.set_defaults(func=cmd_reset)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
