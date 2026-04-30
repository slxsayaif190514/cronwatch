"""CLI helpers for inspecting and resetting alert rate-limit state."""

from __future__ import annotations

import argparse
import sys

from cronwatch.ratelimit import RateLimitStore

_DEFAULT_STORE = "ratelimit.json"
_DEFAULT_WINDOW = 300


def _get_store(path: str) -> RateLimitStore:
    return RateLimitStore(path)


def cmd_show(args: argparse.Namespace) -> int:
    store = _get_store(args.store)
    count = store.alert_count(args.job, window_seconds=args.window)
    limited = store.is_rate_limited(args.job, max_alerts=args.max_alerts, window_seconds=args.window)
    print(f"job:          {args.job}")
    print(f"alerts_in_window: {count}")
    print(f"rate_limited: {limited}")
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    store = _get_store(args.store)
    store.reset(args.job)
    print(f"Rate-limit state cleared for '{args.job}'.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-ratelimit",
        description="Inspect or reset alert rate-limit counters.",
    )
    p.add_argument("--store", default=_DEFAULT_STORE, help="Path to ratelimit JSON store")

    sub = p.add_subparsers(dest="command", required=True)

    show_p = sub.add_parser("show", help="Show rate-limit status for a job")
    show_p.add_argument("job", help="Job name")
    show_p.add_argument("--window", type=int, default=_DEFAULT_WINDOW, help="Window in seconds")
    show_p.add_argument("--max-alerts", type=int, default=3, dest="max_alerts", help="Alert threshold")
    show_p.set_defaults(func=cmd_show)

    reset_p = sub.add_parser("reset", help="Clear rate-limit state for a job")
    reset_p.add_argument("job", help="Job name")
    reset_p.set_defaults(func=cmd_reset)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
