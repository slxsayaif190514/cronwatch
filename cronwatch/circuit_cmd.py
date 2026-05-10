"""CLI commands for inspecting and managing circuit breaker state."""

from __future__ import annotations

import argparse
import sys
from cronwatch.circuit import CircuitStore

_DEFAULT_PATH = "circuit.json"


def _get_store(args: argparse.Namespace) -> CircuitStore:
    return CircuitStore(args.file, threshold=args.threshold, reset_after_s=args.reset_after)


def cmd_show(args: argparse.Namespace):
    store = _get_store(args)
    jobs = [args.job] if args.job else list(store._data.keys())
    if not jobs:
        print("No circuit breaker entries.")
        return
    for job in sorted(jobs):
        entry = store.get(job)
        status = "OPEN" if store.is_open(job) else ("HALF-OPEN" if entry.half_open else "CLOSED")
        opened = entry.opened_at.strftime("%Y-%m-%dT%H:%M:%SZ") if entry.opened_at else "—"
        print(f"{job}: failures={entry.failures} status={status} opened_at={opened}")


def cmd_reset(args: argparse.Namespace):
    store = _get_store(args)
    store.reset(args.job)
    print(f"Circuit reset for job: {args.job}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwatch-circuit", description="Manage circuit breaker state")
    p.add_argument("--file", default=_DEFAULT_PATH)
    p.add_argument("--threshold", type=int, default=5)
    p.add_argument("--reset-after", type=int, default=3600, dest="reset_after")
    sub = p.add_subparsers(dest="cmd")

    sh = sub.add_parser("show", help="Show circuit state")
    sh.add_argument("job", nargs="?", default=None)
    sh.set_defaults(func=cmd_show)

    rs = sub.add_parser("reset", help="Reset circuit for a job")
    rs.add_argument("job")
    rs.set_defaults(func=cmd_reset)

    return p


def main():
    p = build_parser()
    args = p.parse_args()
    if not hasattr(args, "func"):
        p.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
