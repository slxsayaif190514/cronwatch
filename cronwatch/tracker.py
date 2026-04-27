"""Tracks job execution state — last run times, statuses, and missed runs."""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class JobState:
    job_name: str
    last_run: Optional[str] = None  # ISO format
    last_status: Optional[str] = None  # "success" | "failure" | "running"
    consecutive_failures: int = 0
    last_alert_sent: Optional[str] = None  # ISO format

    def last_run_dt(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.last_run) if self.last_run else None

    def last_alert_sent_dt(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.last_alert_sent) if self.last_alert_sent else None


class JobTracker:
    def __init__(self, state_file: str = "/tmp/cronwatch_state.json"):
        self.state_file = state_file
        self._states: dict[str, JobState] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                raw = json.load(f)
            self._states = {k: JobState(**v) for k, v in raw.items()}

    def save(self):
        with open(self.state_file, "w") as f:
            json.dump({k: asdict(v) for k, v in self._states.items()}, f, indent=2)

    def get_state(self, job_name: str) -> JobState:
        if job_name not in self._states:
            self._states[job_name] = JobState(job_name=job_name)
        return self._states[job_name]

    def record_run(self, job_name: str, status: str, run_time: Optional[datetime] = None):
        state = self.get_state(job_name)
        state.last_run = (run_time or datetime.utcnow()).isoformat()
        state.last_status = status
        if status == "failure":
            state.consecutive_failures += 1
        else:
            state.consecutive_failures = 0
        self.save()

    def record_alert_sent(self, job_name: str, sent_at: Optional[datetime] = None):
        state = self.get_state(job_name)
        state.last_alert_sent = (sent_at or datetime.utcnow()).isoformat()
        self.save()

    def all_states(self) -> dict[str, JobState]:
        return dict(self._states)
