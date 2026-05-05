"""CLI commands for managing on-call schedules."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from cronwatch.oncall import OnCallEntry, OnCallStore

_DEFAULT_PATH = "oncall.json"


def _get_store(path: str) -> OnCallStore:
    return OnCallStore(path)


def _parse_dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def cmd_add(args: argparse.Namespace) -> int:
    store = _get_store(args.file)
    entry = OnCallEntry(
        name=args.name,
        email=args.email,
        start=_parse_dt(args.start),
        end=_parse_dt(args.end),
        tags=args.tags or [],
    )
    store.add(entry)
    print(f"Added on-call entry: {args.name} <{args.email}>")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    store = _get_store(args.file)
    if store.remove(args.name):
        print(f"Removed on-call entry: {args.name}")
        return 0
    print(f"No entry found for: {args.name}", file=sys.stderr)
    return 1


def cmd_list(args: argparse.Namespace) -> int:
    store = _get_store(args.file)
    entries = store.get_active(tag=args.tag) if args.active else store.all()
    if not entries:
        print("No on-call entries found.")
        return 0
    for e in entries:
        active = "[active]" if e.is_active() else ""
        tags = ",".join(e.tags) if e.tags else "-"
        print(f"  {e.name} <{e.email}> {e.start.strftime('%Y-%m-%d')} to {e.end.strftime('%Y-%m-%d')} tags={tags} {active}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Manage on-call schedules")
    p.add_argument("--file", default=_DEFAULT_PATH)
    sub = p.add_subparsers(dest="cmd")

    add_p = sub.add_parser("add", help="Add an on-call entry")
    add_p.add_argument("name")
    add_p.add_argument("email")
    add_p.add_argument("start", help="ISO datetime e.g. 2024-01-01T00:00:00Z")
    add_p.add_argument("end", help="ISO datetime e.g. 2024-01-08T00:00:00Z")
    add_p.add_argument("--tags", nargs="*")

    rm_p = sub.add_parser("remove", help="Remove an on-call entry by name")
    rm_p.add_argument("name")

    ls_p = sub.add_parser("list", help="List on-call entries")
    ls_p.add_argument("--active", action="store_true")
    ls_p.add_argument("--tag", default=None)

    return p


def main() -> None:
    p = build_parser()
    args = p.parse_args()
    dispatch = {"add": cmd_add, "remove": cmd_remove, "list": cmd_list}
    fn = dispatch.get(args.cmd)
    if fn is None:
        p.print_help()
        sys.exit(1)
    sys.exit(fn(args))


if __name__ == "__main__":
    main()
