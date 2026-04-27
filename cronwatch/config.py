import os
import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JobConfig:
    name: str
    schedule: str  # cron expression e.g. "*/5 * * * *"
    max_delay_seconds: int = 300
    alert_on_failure: bool = True
    alert_on_delay: bool = True
    tags: List[str] = field(default_factory=list)


@dataclass
class AlertConfig:
    email: Optional[str] = None
    webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None


@dataclass
class Config:
    jobs: List[JobConfig] = field(default_factory=list)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    check_interval_seconds: int = 60
    state_file: str = "/var/lib/cronwatch/state.json"
    log_file: str = "/var/log/cronwatch/cronwatch.log"


def load_config(path: str) -> Config:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        try:
            raw = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file '{path}': {e}") from e

    if not isinstance(raw, dict):
        raise ValueError(f"Config file '{path}' must contain a JSON object at the top level")

    jobs = [
        JobConfig(
            name=j["name"],
            schedule=j["schedule"],
            max_delay_seconds=j.get("max_delay_seconds", 300),
            alert_on_failure=j.get("alert_on_failure", True),
            alert_on_delay=j.get("alert_on_delay", True),
            tags=j.get("tags", []),
        )
        for j in raw.get("jobs", [])
    ]

    alert_raw = raw.get("alerts", {})
    alerts = AlertConfig(
        email=alert_raw.get("email"),
        webhook_url=alert_raw.get("webhook_url"),
        slack_channel=alert_raw.get("slack_channel"),
    )

    return Config(
        jobs=jobs,
        alerts=alerts,
        check_interval_seconds=raw.get("check_interval_seconds", 60),
        state_file=raw.get("state_file", "/var/lib/cronwatch/state.json"),
        log_file=raw.get("log_file", "/var/log/cronwatch/cronwatch.log"),
    )
