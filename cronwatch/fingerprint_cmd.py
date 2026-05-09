"""CLI commands for inspecting and managing failure fingerprints."""

from __future__ import annotations

import argparse
import sys

from cronwatch.fingerprint import FingerprintStore

DEFAULT_PATH = "fingerprints.json"


def _get_store(path: str) -> FingerprintStore:
    return FingerprintStore(path)


def cmd_show(ns: argparse.Namespace) -> None:
    store = _get_store(ns.file)
    entries = store.get_all(job=ns.job or None)
    if not entries:
        print("No fingerprints recorded.")
        return
    for e in entries:
        print(f"[{e.fingerprint}] {e.job}")
        print(f"  message   : {e.message}")
        print(f"  count     : {e.count}")
        print(f"  first_seen: {e.first_seen.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"  last_seen : {e.last_seen.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print()


def cmd_reset(ns: argparse.Namespace) -> None:
    store = _get_store(ns.file)
    ok = store.reset(ns.job, ns.fingerprint)
    if ok:
        print(f"Cleared fingerprint {ns.fingerprint} for job '{ns.job}'.")
    else:
        print(f"Fingerprint {ns.fingerprint} not found for job '{ns.job}'.")
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cronwatch-fingerprint", description="Manage failure fingerprints")
    parser.add_argument("--file", default=DEFAULT_PATH, help="Path to fingerprint store")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_show = sub.add_parser("show", help="Show recorded fingerprints")
    p_show.add_argument("--job", default="", help="Filter by job name")
    p_show.set_defaults(func=cmd_show)

    p_reset = sub.add_parser("reset", help="Remove a fingerprint entry")
    p_reset.add_argument("job", help="Job name")
    p_reset.add_argument("fingerprint", help="Fingerprint hex digest")
    p_reset.set_defaults(func=cmd_reset)

    return parser


def main() -> None:
    parser = build_parser()
    ns = parser.parse_args()
    ns.func(ns)


if __name__ == "__main__":
    main()
