"""On-call schedule management for alert routing."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


@dataclass
class OnCallEntry:
    name: str
    email: str
    start: datetime
    end: datetime
    tags: List[str]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["start"] = _fmt(self.start)
        d["end"] = _fmt(self.end)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "OnCallEntry":
        return cls(
            name=d["name"],
            email=d["email"],
            start=_parse(d["start"]),
            end=_parse(d["end"]),
            tags=d.get("tags", []),
        )

    def is_active(self, at: Optional[datetime] = None) -> bool:
        now = at or _utcnow()
        return self.start <= now <= self.end


class OnCallStore:
    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._entries: List[OnCallEntry] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            data = json.loads(self._path.read_text())
            self._entries = [OnCallEntry.from_dict(e) for e in data]

    def _save(self) -> None:
        self._path.write_text(json.dumps([e.to_dict() for e in self._entries], indent=2))

    def add(self, entry: OnCallEntry) -> None:
        self._entries.append(entry)
        self._save()

    def remove(self, name: str) -> bool:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.name != name]
        if len(self._entries) < before:
            self._save()
            return True
        return False

    def get_active(self, at: Optional[datetime] = None, tag: Optional[str] = None) -> List[OnCallEntry]:
        results = [e for e in self._entries if e.is_active(at)]
        if tag:
            results = [e for e in results if tag in e.tags]
        return results

    def all(self) -> List[OnCallEntry]:
        return list(self._entries)
