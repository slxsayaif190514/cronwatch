"""Audit log — append-only record of significant cronwatch events."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional


DEFAULT_AUDIT_FILE = "/var/log/cronwatch/audit.jsonl"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


class AuditEntry:
    def __init__(self, event: str, job: Optional[str], detail: str, ts: Optional[datetime] = None):
        self.event = event
        self.job = job
        self.detail = detail
        self.ts = ts or _utcnow()

    def to_dict(self) -> dict:
        return {
            "ts": _fmt(self.ts),
            "event": self.event,
            "job": self.job,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AuditEntry":
        return cls(
            event=d["event"],
            job=d.get("job"),
            detail=d.get("detail", ""),
            ts=_parse(d["ts"]),
        )


class AuditLog:
    def __init__(self, path: str = DEFAULT_AUDIT_FILE):
        self._path = path

    def append(self, event: str, job: Optional[str] = None, detail: str = "") -> AuditEntry:
        entry = AuditEntry(event=event, job=job, detail=detail)
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        with open(self._path, "a") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")
        return entry

    def read(self, job: Optional[str] = None, event: Optional[str] = None) -> List[AuditEntry]:
        if not os.path.exists(self._path):
            return []
        entries: List[AuditEntry] = []
        with open(self._path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = AuditEntry.from_dict(json.loads(line))
                except (KeyError, ValueError):
                    continue
                if job is not None and e.job != job:
                    continue
                if event is not None and e.event != event:
                    continue
                entries.append(e)
        return entries

    def clear(self) -> int:
        if not os.path.exists(self._path):
            return 0
        entries = self.read()
        open(self._path, "w").close()
        return len(entries)
