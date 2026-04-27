"""Command-line interface for cronwatch daemon."""

import argparse
import logging
import signal
import sys
import time

from cronwatch.config import load_config
from cronwatch.monitor import run_checks
from cronwatch.tracker import JobTracker

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=level,
    )


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="cronwatch",
        description="Monitor cron job execution times and alert on issues.",
    )
    parser.add_argument(
        "-c", "--config",
        default="cronwatch/config_example.json",
        help="Path to JSON config file (default: cronwatch/config_example.json)",
    )
    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run checks once and exit (useful for testing)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    setup_logging(args.verbose)

    logger.info("Loading config from %s", args.config)
    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("Failed to load config: %s", exc)
        return 1

    tracker = JobTracker(state_file=".cronwatch_state.json")

    stop = False

    def _handle_signal(signum, frame):  # noqa: ANN001
        nonlocal stop
        logger.info("Received signal %s, shutting down.", signum)
        stop = True

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("cronwatch started (interval=%ds)", args.interval)
    while not stop:
        run_checks(config, tracker)
        if args.once:
            break
        for _ in range(args.interval):
            if stop:
                break
            time.sleep(1)

    logger.info("cronwatch stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
