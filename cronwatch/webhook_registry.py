"""Registry for named webhook endpoints used by alert dispatch."""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class WebhookEndpoint:
    name: str
    url: str
    secret: Optional[str] = None
    timeout: int = 10
    enabled: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "WebhookEndpoint":
        return cls(
            name=d["name"],
            url=d["url"],
            secret=d.get("secret"),
            timeout=d.get("timeout", 10),
            enabled=d.get("enabled", True),
        )


class WebhookRegistry:
    def __init__(self, path: str):
        self._path = path
        self._endpoints: dict[str, WebhookEndpoint] = {}
        if os.path.exists(path):
            self._load()

    def _load(self) -> None:
        with open(self._path) as f:
            data = json.load(f)
        for item in data.get("webhooks", []):
            ep = WebhookEndpoint.from_dict(item)
            self._endpoints[ep.name] = ep

    def _save(self) -> None:
        data = {"webhooks": [ep.to_dict() for ep in self._endpoints.values()]}
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2)

    def register(self, endpoint: WebhookEndpoint) -> None:
        self._endpoints[endpoint.name] = endpoint
        self._save()

    def get(self, name: str) -> Optional[WebhookEndpoint]:
        return self._endpoints.get(name)

    def remove(self, name: str) -> bool:
        if name in self._endpoints:
            del self._endpoints[name]
            self._save()
            return True
        return False

    def list_enabled(self) -> list[WebhookEndpoint]:
        return [ep for ep in self._endpoints.values() if ep.enabled]

    def all(self) -> list[WebhookEndpoint]:
        return list(self._endpoints.values())
