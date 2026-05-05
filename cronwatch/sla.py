"""SLA tracking — record and query SLA compliance for monitored jobs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


@dataclass
class SLARecord:
    job_name: str
    window_start: datetime
    window_end: datetime
    total_runs: int = 0
    on_time_runs: int = 0

    @property
    def compliance_pct(self) -> float:
        if self.total_runs == 0:
            return 100.0
        return round(100.0 * self.on_time_runs / self.total_runs, 2)

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "window_start": _fmt(self.window_start),
            "window_end": _fmt(self.window_end),
            "total_runs": self.total_runs,
            "on_time_runs": self.on_time_runs,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SLARecord":
        return cls(
            job_name=d["job_name"],
            window_start=_parse(d["window_start"]),
            window_end=_parse(d["window_end"]),
            total_runs=d.get("total_runs", 0),
            on_time_runs=d.get("on_time_runs", 0),
        )


class SLAStore:
    def __init__(self, path: str) -> None:
        self._path = path
        self._records: Dict[str, List[SLARecord]] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        with open(self._path) as fh:
            raw = json.load(fh)
        for job, entries in raw.items():
            self._records[job] = [SLARecord.from_dict(e) for e in entries]

    def _save(self) -> None:
        data = {job: [r.to_dict() for r in recs] for job, recs in self._records.items()}
        with open(self._path, "w") as fh:
            json.dump(data, fh, indent=2)

    def record_run(self, job_name: str, window_start: datetime, window_end: datetime, on_time: bool) -> None:
        key = _fmt(window_start)
        recs = self._records.setdefault(job_name, [])
        for r in recs:
            if _fmt(r.window_start) == key:
                r.total_runs += 1
                if on_time:
                    r.on_time_runs += 1
                self._save()
                return
        rec = SLARecord(job_name, window_start, window_end, total_runs=1, on_time_runs=1 if on_time else 0)
        recs.append(rec)
        self._save()

    def get_records(self, job_name: str) -> List[SLARecord]:
        return list(self._records.get(job_name, []))

    def compliance_for(self, job_name: str) -> Optional[float]:
        recs = self.get_records(job_name)
        if not recs:
            return None
        total = sum(r.total_runs for r in recs)
        on_time = sum(r.on_time_runs for r in recs)
        if total == 0:
            return 100.0
        return round(100.0 * on_time / total, 2)

    def clear(self, job_name: str) -> None:
        self._records.pop(job_name, None)
        self._save()
