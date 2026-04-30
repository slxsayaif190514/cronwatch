"""Configuration loading and dataclasses for cronwatch."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AlertConfig:
    email: Optional[str] = None
    webhook: Optional[str] = None
    cooldown_minutes: int = 30


@dataclass
class JobConfig:
    name: str
    schedule: str
    grace_minutes: int = 5
    tags: List[str] = field(default_factory=list)
    alert: Optional[AlertConfig] = None


@dataclass
class Config:
    jobs: List[JobConfig] = field(default_factory=list)
    alert: Optional[AlertConfig] = None
    state_dir: str = "/tmp/cronwatch"


def _parse_alert(data: Dict[str, Any]) -> AlertConfig:
    return AlertConfig(
        email=data.get("email"),
        webhook=data.get("webhook"),
        cooldown_minutes=int(data.get("cooldown_minutes", 30)),
    )


def _parse_job(data: Dict[str, Any]) -> JobConfig:
    alert_data = data.get("alert")
    return JobConfig(
        name=data["name"],
        schedule=data["schedule"],
        grace_minutes=int(data.get("grace_minutes", 5)),
        tags=list(data.get("tags", [])),
        alert=_parse_alert(alert_data) if alert_data else None,
    )


def load_config(path: str) -> Config:
    with open(path) as fh:
        raw = json.load(fh)

    alert_data = raw.get("alert")
    return Config(
        jobs=[_parse_job(j) for j in raw.get("jobs", [])],
        alert=_parse_alert(alert_data) if alert_data else None,
        state_dir=raw.get("state_dir", "/tmp/cronwatch"),
    )
