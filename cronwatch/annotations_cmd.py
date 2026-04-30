"""CLI sub-commands for managing job annotations."""

from __future__ import annotations

import argparse
import os
import sys

from cronwatch.annotations import AnnotationStore

_DEFAULT_FILE = os.environ.get("CRONWATCH_ANNOTATIONS", "annotations.json")


def _get_store(path: str) -> AnnotationStore:
    return AnnotationStore(path)


def cmd_add(args: argparse.Namespace) -> int:
    store = _get_store(args.file)
    ann = store.add(args.job, args.note, author=args.author)
    print(f"[+] Annotation added for '{ann.job_name}' at {ann.created_at.isoformat()}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = _get_store(args.file)
    entries = store.get(args.job) if args.job else store.all()
    if not entries:
        print("No annotations found.")
        return 0
    for a in entries:
        print(f"[{a.created_at.strftime('%Y-%m-%d %H:%M')}] ({a.author}) {a.job_name}: {a.note}")
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    store = _get_store(args.file)
    removed = store.clear(args.job)
    print(f"Removed {removed} annotation(s) for '{args.job}'.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwatch-annotations", description="Manage job annotations")
    p.add_argument("--file", default=_DEFAULT_FILE, help="Annotations file path")
    sub = p.add_subparsers(dest="command")

    add_p = sub.add_parser("add", help="Add an annotation")
    add_p.add_argument("job", help="Job name")
    add_p.add_argument("note", help="Annotation text")
    add_p.add_argument("--author", default="system", help="Author name")

    list_p = sub.add_parser("list", help="List annotations")
    list_p.add_argument("job", nargs="?", default=None, help="Filter by job name")

    clear_p = sub.add_parser("clear", help="Clear annotations for a job")
    clear_p.add_argument("job", help="Job name")

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {"add": cmd_add, "list": cmd_list, "clear": cmd_clear}
    if args.command not in dispatch:
        parser.print_help()
        return 1
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
