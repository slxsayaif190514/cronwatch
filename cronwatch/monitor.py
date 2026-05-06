"""Core monitor loop — checks each job and fires alerts when needed."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from cronwatch.alerts import build_failure_message, build_overdue_message, send_alert
from cronwatch.config import Config
from cronwatch.schedule import is_overdue
from cronwatch.tracker import JobTracker

logger = logging.getLogger(__name__)

# Minimum gap between repeated alerts for the same job (minutes)
DEFAULT_ALERT_COOLDOWN_MINUTES = 30


def run_checks(config: Config, tracker: JobTracker, now: Optional[datetime] = None):
    """Check all configured jobs and send alerts where necessary."""
    now = now or datetime.utcnow()

    for job in config.jobs:
        state = tracker.get_state(job.name)
        last_run = state.last_run_dt()

        # --- overdue check ---
        if is_overdue(job.schedule, last_run, job.grace_minutes, now):
            if _should_alert(state, now, config.alerts.cooldown_minutes):
                from cronwatch.schedule import get_last_expected_run
                expected = get_last_expected_run(job.schedule, now)
                minutes_late = (now - expected).total_seconds() / 60 if expected else 0
                subject, body = build_overdue_message(job.name, minutes_late)
                if send_alert(config.alerts, subject, body):
                    tracker.record_alert_sent(job.name, now)
                    logger.info("Overdue alert sent for job '%s'", job.name)
            else:
                logger.debug("Skipping alert for '%s' — cooldown active", job.name)

        # --- consecutive failure check ---
        if state.consecutive_failures >= job.failure_threshold:
            if _should_alert(state, now, config.alerts.cooldown_minutes):
                subject, body = build_failure_message(job.name, state.consecutive_failures)
                if send_alert(config.alerts, subject, body):
                    tracker.record_alert_sent(job.name, now)
                    logger.info("Failure alert sent for job '%s'", job.name)


def _should_alert(state, now: datetime, cooldown_minutes: Optional[int]) -> bool:
    """Return True if enough time has passed since the last alert for this job.

    Args:
        state: The current job state, used to retrieve the last alert timestamp.
        now: The current UTC datetime.
        cooldown_minutes: How many minutes must elapse before re-alerting.
            Falls back to DEFAULT_ALERT_COOLDOWN_MINUTES if None or zero.

    Returns:
        True if no alert has been sent yet, or the cooldown period has elapsed.
    """
    cooldown = timedelta(minutes=cooldown_minutes or DEFAULT_ALERT_COOLDOWN_MINUTES)
    last_alert = state.last_alert_sent_dt()
    if last_alert is None:
        return True
    return (now - last_alert) >= cooldown
