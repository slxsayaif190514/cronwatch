"""Job annotation support — attach freeform notes to job runs for audit/debug purposes."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


class Annotation:
    def __init__(self, job_name: str, note: str, author: str = "system", created_at: Optional[datetime] = None):
        self.job_name = job_name
        self.note = note
        self.author = author
        self.created_at = created_at or _utcnow()

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "note": self.note,
            "author": self.author,
            "created_at": _fmt(self.created_at),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Annotation":
        return cls(
            job_name=d["job_name"],
            note=d["note"],
            author=d.get("author", "system"),
            created_at=_parse(d["created_at"]),
        )


class AnnotationStore:
    def __init__(self, path: str):
        self._path = path
        self._entries: List[Annotation] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        with open(self._path) as fh:
            raw = json.load(fh)
        self._entries = [Annotation.from_dict(r) for r in raw]

    def _save(self) -> None:
        with open(self._path, "w") as fh:
            json.dump([a.to_dict() for a in self._entries], fh, indent=2)

    def add(self, job_name: str, note: str, author: str = "system") -> Annotation:
        ann = Annotation(job_name=job_name, note=note, author=author)
        self._entries.append(ann)
        self._save()
        return ann

    def get(self, job_name: str) -> List[Annotation]:
        return [a for a in self._entries if a.job_name == job_name]

    def all(self) -> List[Annotation]:
        return list(self._entries)

    def clear(self, job_name: str) -> int:
        before = len(self._entries)
        self._entries = [a for a in self._entries if a.job_name != job_name]
        self._save()
        return before - len(self._entries)
