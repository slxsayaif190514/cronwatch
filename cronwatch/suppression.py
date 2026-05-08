"""Alert suppression rules — temporarily mute alerts for specific jobs."""

from __future__ import annotations

import json
from dataclasses import dataclass
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
class SuppressionRule:
    job_name: str
    reason: str
    created_at: datetime
    expires_at: Optional[datetime]

    def is_active(self, now: Optional[datetime] = None) -> bool:
        now = now or _utcnow()
        if self.expires_at is None:
            return True
        return now < self.expires_at

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "reason": self.reason,
            "created_at": _fmt(self.created_at),
            "expires_at": _fmt(self.expires_at) if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SuppressionRule":
        return cls(
            job_name=d["job_name"],
            reason=d["reason"],
            created_at=_parse(d["created_at"]),
            expires_at=_parse(d["expires_at"]) if d.get("expires_at") else None,
        )


class SuppressionStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._rules: List[SuppressionRule] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            data = json.loads(self._path.read_text())
            self._rules = [SuppressionRule.from_dict(r) for r in data.get("rules", [])]

    def _save(self) -> None:
        self._path.write_text(json.dumps({"rules": [r.to_dict() for r in self._rules]}, indent=2))

    def add(self, job_name: str, reason: str, expires_at: Optional[datetime] = None) -> SuppressionRule:
        rule = SuppressionRule(
            job_name=job_name,
            reason=reason,
            created_at=_utcnow(),
            expires_at=expires_at,
        )
        self._rules.append(rule)
        self._save()
        return rule

    def remove(self, job_name: str) -> int:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.job_name != job_name]
        self._save()
        return before - len(self._rules)

    def is_suppressed(self, job_name: str, now: Optional[datetime] = None) -> bool:
        return any(r.job_name == job_name and r.is_active(now) for r in self._rules)

    def active_rules(self, now: Optional[datetime] = None) -> List[SuppressionRule]:
        return [r for r in self._rules if r.is_active(now)]

    def all_rules(self) -> List[SuppressionRule]:
        return list(self._rules)

    def purge_expired(self, now: Optional[datetime] = None) -> int:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.is_active(now)]
        self._save()
        return before - len(self._rules)
