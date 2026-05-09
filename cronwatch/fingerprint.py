"""Job failure fingerprinting — group repeated failures by their error signature."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def fingerprint_error(message: str) -> str:
    """Return a short hex digest identifying an error message."""
    normalized = " ".join(message.lower().split())
    return hashlib.sha1(normalized.encode()).hexdigest()[:12]


class FingerprintEntry:
    def __init__(self, fingerprint: str, job: str, message: str, count: int, first_seen: datetime, last_seen: datetime):
        self.fingerprint = fingerprint
        self.job = job
        self.message = message
        self.count = count
        self.first_seen = first_seen
        self.last_seen = last_seen

    def to_dict(self) -> dict:
        return {
            "fingerprint": self.fingerprint,
            "job": self.job,
            "message": self.message,
            "count": self.count,
            "first_seen": _fmt(self.first_seen),
            "last_seen": _fmt(self.last_seen),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FingerprintEntry":
        return cls(
            fingerprint=d["fingerprint"],
            job=d["job"],
            message=d["message"],
            count=d["count"],
            first_seen=_parse(d["first_seen"]),
            last_seen=_parse(d["last_seen"]),
        )


class FingerprintStore:
    def __init__(self, path: str):
        self._path = Path(path)
        self._data: Dict[str, FingerprintEntry] = {}
        self._load()

    def _load(self):
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._data = {k: FingerprintEntry.from_dict(v) for k, v in raw.items()}

    def _save(self):
        self._path.write_text(json.dumps({k: v.to_dict() for k, v in self._data.items()}, indent=2))

    def record(self, job: str, message: str) -> FingerprintEntry:
        fp = fingerprint_error(message)
        now = _utcnow()
        key = f"{job}:{fp}"
        if key in self._data:
            entry = self._data[key]
            entry.count += 1
            entry.last_seen = now
        else:
            entry = FingerprintEntry(fp, job, message, 1, now, now)
            self._data[key] = entry
        self._save()
        return entry

    def get(self, job: str, fingerprint: str) -> Optional[FingerprintEntry]:
        return self._data.get(f"{job}:{fingerprint}")

    def get_all(self, job: Optional[str] = None) -> List[FingerprintEntry]:
        entries = list(self._data.values())
        if job:
            entries = [e for e in entries if e.job == job]
        return sorted(entries, key=lambda e: e.last_seen, reverse=True)

    def reset(self, job: str, fingerprint: str) -> bool:
        key = f"{job}:{fingerprint}"
        if key in self._data:
            del self._data[key]
            self._save()
            return True
        return False
