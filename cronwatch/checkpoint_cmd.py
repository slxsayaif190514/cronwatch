"""CLI sub-commands for inspecting and managing job checkpoints."""

from __future__ import annotations

import argparse
import sys
from datetime import timezone

from cronwatch.checkpoint import CheckpointStore

DEFAULT_PATH = "checkpoints.json"


def _get_store(path: str) -> CheckpointStore:
    return CheckpointStore(path)


def cmd_show(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    entries = store.all()
    if not entries:
        print("No checkpoints recorded.")
        return
    jobs = [args.job] if getattr(args, "job", None) else sorted(entries)
    for name in jobs:
        if name not in entries:
            print(f"{name}: (no checkpoint)")
            continue
        dt = entries[name]
        age = store.age_seconds(name)
        age_str = f"{age:.0f}s ago" if age is not None else "unknown"
        print(f"{name}: {dt.strftime('%Y-%m-%dT%H:%M:%SZ')}  ({age_str})")


def cmd_set(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    ts = store.set(args.job)
    print(f"Checkpoint set for '{args.job}': {ts.strftime('%Y-%m-%dT%H:%M:%SZ')}")


def cmd_remove(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    removed = store.remove(args.job)
    if removed:
        print(f"Checkpoint removed for '{args.job}'.")
    else:
        print(f"No checkpoint found for '{args.job}'.")
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Manage cronwatch job checkpoints")
    p.add_argument("--file", default=DEFAULT_PATH, help="Checkpoint store path")
    sub = p.add_subparsers(dest="cmd", required=True)

    sh = sub.add_parser("show", help="Show checkpoints")
    sh.add_argument("job", nargs="?", default=None, help="Specific job name")
    sh.set_defaults(func=cmd_show)

    st = sub.add_parser("set", help="Set checkpoint for a job to now")
    st.add_argument("job", help="Job name")
    st.set_defaults(func=cmd_set)

    rm = sub.add_parser("remove", help="Remove checkpoint for a job")
    rm.add_argument("job", help="Job name")
    rm.set_defaults(func=cmd_remove)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
