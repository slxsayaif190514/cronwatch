from datetime import datetime, timezone
from typing import Optional
from croniter import croniter


def get_last_expected_run(schedule: str, now: Optional[datetime] = None) -> datetime:
    """Return the most recent scheduled time before or at `now`."""
    if now is None:
        now = datetime.now(timezone.utc)

    # croniter works with naive datetimes; strip tzinfo for calculation
    now_naive = now.replace(tzinfo=None)
    cron = croniter(schedule, now_naive)
    last_run = cron.get_prev(datetime)
    return last_run.replace(tzinfo=timezone.utc)


def get_next_expected_run(schedule: str, now: Optional[datetime] = None) -> datetime:
    """Return the next scheduled time after `now`."""
    if now is None:
        now = datetime.now(timezone.utc)

    now_naive = now.replace(tzinfo=None)
    cron = croniter(schedule, now_naive)
    next_run = cron.get_next(datetime)
    return next_run.replace(tzinfo=timezone.utc)


def is_overdue(schedule: str, last_seen: Optional[datetime], max_delay_seconds: int,
               now: Optional[datetime] = None) -> bool:
    """Return True if the job is overdue based on last seen execution time."""
    if now is None:
        now = datetime.now(timezone.utc)

    expected = get_last_expected_run(schedule, now)

    if last_seen is None:
        # Never ran — check if the expected run is past the grace period
        delay = (now - expected).total_seconds()
        return delay > max_delay_seconds

    # Job ran before the last expected slot
    if last_seen < expected:
        delay = (now - expected).total_seconds()
        return delay > max_delay_seconds

    return False
