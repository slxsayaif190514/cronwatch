"""Dead-letter queue: store and replay alerts that failed to dispatch."""

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


@dataclass
class DeadLetter:
    job_name: str
    channel: str
    message: str
    failed_at: str
    attempts: int = 1
    last_error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "DeadLetter":
        return cls(**d)


class DeadLetterQueue:
    def __init__(self, path: str) -> None:
        self._path = path
        self._entries: List[DeadLetter] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            self._entries = []
            return
        with open(self._path) as fh:
            raw = json.load(fh)
        self._entries = [DeadLetter.from_dict(r) for r in raw]

    def _save(self) -> None:
        with open(self._path, "w") as fh:
            json.dump([e.to_dict() for e in self._entries], fh, indent=2)

    def push(self, job_name: str, channel: str, message: str, error: str) -> DeadLetter:
        entry = DeadLetter(
            job_name=job_name,
            channel=channel,
            message=message,
            failed_at=_fmt(_utcnow()),
            attempts=1,
            last_error=error,
        )
        self._entries.append(entry)
        self._save()
        return entry

    def all(self) -> List[DeadLetter]:
        return list(self._entries)

    def remove(self, job_name: str, channel: str) -> bool:
        before = len(self._entries)
        self._entries = [
            e for e in self._entries
            if not (e.job_name == job_name and e.channel == channel)
        ]
        if len(self._entries) < before:
            self._save()
            return True
        return False

    def increment_attempt(self, job_name: str, channel: str, error: str) -> None:
        for e in self._entries:
            if e.job_name == job_name and e.channel == channel:
                e.attempts += 1
                e.last_error = error
        self._save()

    def clear(self) -> None:
        self._entries = []
        self._save()
