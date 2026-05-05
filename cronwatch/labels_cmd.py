"""CLI commands for inspecting job labels."""

from __future__ import annotations

import argparse
import json
import sys

from cronwatch.config import load_config
from cronwatch.labels import (
    filter_jobs,
    get_all_label_keys,
    label_summary,
    parse_label,
)


def cmd_list(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    keys = get_all_label_keys(config)
    if not keys:
        print("No labels defined.")
        return 0
    for key in keys:
        print(key)
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    summary = label_summary(config)
    if not summary:
        print("No labels defined.")
        return 0
    if args.json:
        print(json.dumps(summary, indent=2))
        return 0
    for key in sorted(summary):
        for value in sorted(summary[key]):
            jobs = ", ".join(summary[key][value])
            print(f"{key}={value}: {jobs}")
    return 0


def cmd_filter(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    try:
        jobs = filter_jobs(config, args.selector)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if not jobs:
        print("No matching jobs.")
        return 0
    for job in jobs:
        print(job.name)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwatch-labels", description="Manage job labels")
    p.add_argument("--config", required=True, help="Path to config file")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all label keys")

    sp = sub.add_parser("summary", help="Show label key/value breakdown")
    sp.add_argument("--json", action="store_true", help="Output as JSON")

    fp = sub.add_parser("filter", help="Filter jobs by label selector (key=value)")
    fp.add_argument("selector", help="Label selector, e.g. env=prod")

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {"list": cmd_list, "summary": cmd_summary, "filter": cmd_filter}
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
