"""CLI commands for managing job alert lockouts."""

import argparse
import sys

from cronwatch.lockout import LockoutStore

_DEFAULT_PATH = "lockouts.json"


def _get_store(path: str) -> LockoutStore:
    return LockoutStore(path)


def cmd_lock(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    entry = store.lock(args.job, reason=args.reason, locked_by=args.by)
    print(f"Locked '{entry.job_name}' at {entry.locked_at.isoformat()} by {entry.locked_by}")
    print(f"  Reason: {entry.reason}")


def cmd_unlock(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    removed = store.unlock(args.job)
    if removed:
        print(f"Unlocked '{args.job}'")
    else:
        print(f"Job '{args.job}' was not locked", file=sys.stderr)
        sys.exit(1)


def cmd_list(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    entries = store.all()
    if not entries:
        print("No locked jobs.")
        return
    for e in entries:
        print(f"{e.job_name:30s}  locked={e.locked_at.strftime('%Y-%m-%d %H:%M')}  by={e.locked_by}")
        print(f"  reason: {e.reason}")


def cmd_show(args: argparse.Namespace) -> None:
    store = _get_store(args.file)
    entry = store.get(args.job)
    if entry is None:
        print(f"Job '{args.job}' is not locked.")
        return
    print(f"Job:       {entry.job_name}")
    print(f"Locked at: {entry.locked_at.isoformat()}")
    print(f"Locked by: {entry.locked_by}")
    print(f"Reason:    {entry.reason}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Manage job alert lockouts")
    p.add_argument("--file", default=_DEFAULT_PATH, help="Lockout store path")
    sub = p.add_subparsers(dest="cmd", required=True)

    lk = sub.add_parser("lock", help="Lock a job")
    lk.add_argument("job")
    lk.add_argument("--reason", default="manually locked", help="Reason for lockout")
    lk.add_argument("--by", default="admin", help="Who is locking")
    lk.set_defaults(func=cmd_lock)

    ul = sub.add_parser("unlock", help="Unlock a job")
    ul.add_argument("job")
    ul.set_defaults(func=cmd_unlock)

    ls = sub.add_parser("list", help="List all locked jobs")
    ls.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="Show lockout details for a job")
    sh.add_argument("job")
    sh.set_defaults(func=cmd_show)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
