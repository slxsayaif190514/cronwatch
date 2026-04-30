"""CLI commands for managing job dependencies."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from cronwatch.dependency import DependencyStore

DEFAULT_DEPS_FILE = "deps.json"


def _get_store(path: str) -> DependencyStore:
    return DependencyStore(path)


def cmd_set(args: argparse.Namespace) -> int:
    store = _get_store(args.deps_file)
    deps = args.depends_on or []
    store.set_dependencies(args.job, deps)
    print(f"Set dependencies for '{args.job}': {deps}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    store = _get_store(args.deps_file)
    state = store.get(args.job)
    if state is None:
        print(f"No dependency info for '{args.job}'.")
        return 1
    print(f"Job:         {state.job_name}")
    print(f"Depends on:  {', '.join(state.depends_on) if state.depends_on else '(none)'}")
    ls = state.last_satisfied.isoformat() if state.last_satisfied else "never"
    print(f"Last satisfied: {ls}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    store = _get_store(args.deps_file)
    store.set_dependencies(args.job, [])
    print(f"Cleared dependencies for '{args.job}'.")
    return 0


def build_parser(deps_file: str = DEFAULT_DEPS_FILE) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwatch-deps", description="Manage job dependencies")
    p.add_argument("--deps-file", default=deps_file)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("set", help="Set dependencies for a job")
    s.add_argument("job")
    s.add_argument("depends_on", nargs="*", metavar="DEP")
    s.set_defaults(func=cmd_set)

    sh = sub.add_parser("show", help="Show dependencies for a job")
    sh.add_argument("job")
    sh.set_defaults(func=cmd_show)

    rm = sub.add_parser("remove", help="Remove all dependencies for a job")
    rm.add_argument("job")
    rm.set_defaults(func=cmd_remove)

    return p


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
