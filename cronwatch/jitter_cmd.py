"""CLI commands for inspecting jitter data."""
from __future__ import annotations

import argparse
import sys

from cronwatch.jitter import JitterStore

DEFAULT_PATH = "jitter.json"


def _get_store(path: str) -> JitterStore:
    return JitterStore(path)


def cmd_show(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    jobs = [args.job] if args.job else store.all_jobs()
    if not jobs:
        print("No jitter data recorded.")
        return
    for name in jobs:
        samples = store.get_samples(name)
        avg = store.avg_jitter(name)
        flag = " [HIGH]" if store.is_high_jitter(name, args.threshold) else ""
        avg_str = f"{avg:.1f}s" if avg is not None else "n/a"
        print(f"{name}: samples={len(samples)}, avg_jitter={avg_str}{flag}")


def cmd_reset(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    if args.job:
        store.reset(args.job)
        print(f"Jitter data cleared for '{args.job}'.")
    else:
        for name in store.all_jobs():
            store.reset(name)
        print("All jitter data cleared.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Inspect cronwatch jitter data")
    p.add_argument("--file", default=DEFAULT_PATH, help="Jitter store path")
    sub = p.add_subparsers(dest="command")

    show = sub.add_parser("show", help="Show jitter stats")
    show.add_argument("job", nargs="?", help="Specific job name")
    show.add_argument(
        "--threshold", type=float, default=60.0,
        help="High-jitter threshold in seconds (default: 60)"
    )
    show.set_defaults(func=cmd_show)

    rst = sub.add_parser("reset", help="Clear jitter samples")
    rst.add_argument("job", nargs="?", help="Specific job name (omit for all)")
    rst.set_defaults(func=cmd_reset)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "func", None):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
