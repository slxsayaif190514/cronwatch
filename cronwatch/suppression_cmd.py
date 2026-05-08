"""CLI commands for managing alert suppression rules."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from cronwatch.suppression import SuppressionStore

_DEFAULT_PATH = Path("suppression.json")


def _get_store(path: str) -> SuppressionStore:
    return SuppressionStore(Path(path))


def _parse_dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def cmd_add(ns: argparse.Namespace) -> None:
    store = _get_store(ns.file)
    expires = _parse_dt(ns.expires) if ns.expires else None
    rule = store.add(ns.job, ns.reason, expires_at=expires)
    exp_str = rule.expires_at.strftime("%Y-%m-%dT%H:%M:%SZ") if rule.expires_at else "never"
    print(f"Suppressed '{ns.job}' until {exp_str}: {ns.reason}")


def cmd_remove(ns: argparse.Namespace) -> None:
    store = _get_store(ns.file)
    removed = store.remove(ns.job)
    if removed:
        print(f"Removed {removed} suppression rule(s) for '{ns.job}'.")
    else:
        print(f"No suppression rules found for '{ns.job}'.")


def cmd_list(ns: argparse.Namespace) -> None:
    store = _get_store(ns.file)
    rules = store.active_rules() if not ns.all else store.all_rules()
    if not rules:
        print("No suppression rules.")
        return
    for r in rules:
        exp = r.expires_at.strftime("%Y-%m-%dT%H:%M:%SZ") if r.expires_at else "never"
        status = "active" if r.is_active() else "expired"
        print(f"  [{status}] {r.job_name}  expires={exp}  reason={r.reason}")


def cmd_purge(ns: argparse.Namespace) -> None:
    store = _get_store(ns.file)
    removed = store.purge_expired()
    print(f"Purged {removed} expired suppression rule(s).")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Manage alert suppression rules")
    p.add_argument("--file", default=str(_DEFAULT_PATH), help="Path to suppression store")
    sub = p.add_subparsers(dest="cmd", required=True)

    add_p = sub.add_parser("add", help="Suppress alerts for a job")
    add_p.add_argument("job")
    add_p.add_argument("reason")
    add_p.add_argument("--expires", default=None, help="Expiry datetime (ISO8601 UTC)")
    add_p.set_defaults(func=cmd_add)

    rm_p = sub.add_parser("remove", help="Remove suppression for a job")
    rm_p.add_argument("job")
    rm_p.set_defaults(func=cmd_remove)

    ls_p = sub.add_parser("list", help="List suppression rules")
    ls_p.add_argument("--all", action="store_true", help="Include expired rules")
    ls_p.set_defaults(func=cmd_list)

    purge_p = sub.add_parser("purge", help="Remove all expired rules")
    purge_p.set_defaults(func=cmd_purge)

    return p


def main() -> None:
    parser = build_parser()
    ns = parser.parse_args()
    ns.func(ns)


if __name__ == "__main__":
    main()
