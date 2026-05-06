"""CLI for inspecting job duration trends."""

from __future__ import annotations

import argparse
import os
import sys

from cronwatch.trend import TrendStore

_DEFAULT_PATH = os.environ.get("CRONWATCH_TREND_FILE", "trend.json")
_DEFAULT_THRESHOLD = 1.0


def _get_store(path: str) -> TrendStore:
    return TrendStore(path)


def cmd_show(ns: argparse.Namespace) -> None:
    store = _get_store(ns.file)
    jobs = [ns.job] if ns.job else list(store._data.keys())
    if not jobs:
        print("No trend data recorded yet.")
        return
    for job in sorted(jobs):
        pts = store.get_points(job)
        slope = store.slope(job)
        trending = store.is_trending_up(job, ns.threshold)
        durations = [p.duration_s for p in pts]
        avg = sum(durations) / len(durations) if durations else 0.0
        flag = " [TRENDING UP]" if trending else ""
        print(f"{job}: samples={len(pts)} avg={avg:.2f}s slope={slope:.4f}s/run{flag}")


def cmd_reset(ns: argparse.Namespace) -> None:
    store = _get_store(ns.file)
    if ns.job:
        store.clear(ns.job)
        print(f"Cleared trend data for {ns.job}")
    else:
        for job in list(store._data.keys()):
            store.clear(job)
        print("Cleared all trend data")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Inspect job duration trends")
    p.add_argument("--file", default=_DEFAULT_PATH, help="Trend store file")
    sub = p.add_subparsers(dest="cmd")

    show = sub.add_parser("show", help="Show trend info")
    show.add_argument("job", nargs="?", help="Job name (omit for all)")
    show.add_argument("--threshold", type=float, default=_DEFAULT_THRESHOLD)
    show.set_defaults(func=cmd_show)

    rst = sub.add_parser("reset", help="Clear trend data")
    rst.add_argument("job", nargs="?", help="Job name (omit for all)")
    rst.set_defaults(func=cmd_reset)

    return p


def main() -> None:
    p = build_parser()
    ns = p.parse_args()
    if not hasattr(ns, "func"):
        p.print_help()
        sys.exit(1)
    ns.func(ns)


if __name__ == "__main__":
    main()
