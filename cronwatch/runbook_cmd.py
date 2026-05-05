"""CLI commands for managing runbook entries."""

from __future__ import annotations

import argparse
import os
import sys

from cronwatch.runbook import RunbookStore

_DEFAULT_PATH = os.environ.get("CRONWATCH_RUNBOOK_FILE", "runbook.json")


def _get_store(path: str) -> RunbookStore:
    return RunbookStore(path)


def cmd_set(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    entry = store.set(args.job, args.url, args.notes or "")
    print(f"Runbook set for '{entry.job_name}': {entry.url}")
    if entry.notes:
        print(f"  Notes: {entry.notes}")


def cmd_show(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    if args.job:
        entry = store.get(args.job)
        if entry is None:
            print(f"No runbook entry for '{args.job}'.")
            sys.exit(1)
        print(f"{entry.job_name}")
        print(f"  URL:     {entry.url}")
        print(f"  Notes:   {entry.notes or '(none)'}")
        print(f"  Updated: {entry.updated_at}")
    else:
        entries = store.all()
        if not entries:
            print("No runbook entries.")
            return
        for e in entries:
            notes_preview = (e.notes[:40] + "...") if len(e.notes) > 40 else e.notes
            print(f"  {e.job_name:<30} {e.url}  {notes_preview}")


def cmd_remove(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    if store.remove(args.job):
        print(f"Removed runbook entry for '{args.job}'.")
    else:
        print(f"No entry found for '{args.job}'.")
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Manage cronwatch runbook links")
    p.add_argument("--file", default=_DEFAULT_PATH, help="Runbook store path")
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("set", help="Add or update a runbook entry")
    ps.add_argument("job", help="Job name")
    ps.add_argument("url", help="Runbook URL")
    ps.add_argument("--notes", default="", help="Optional notes")
    ps.set_defaults(func=cmd_set)

    psh = sub.add_parser("show", help="Show runbook entries")
    psh.add_argument("job", nargs="?", default=None, help="Job name (omit for all)")
    psh.set_defaults(func=cmd_show)

    pr = sub.add_parser("remove", help="Remove a runbook entry")
    pr.add_argument("job", help="Job name")
    pr.set_defaults(func=cmd_remove)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
