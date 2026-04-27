"""Simple HTTP healthcheck endpoint for cronwatch daemon."""

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def _build_status(get_tracker_fn: Callable) -> dict:
    """Build a status dict from the current tracker state."""
    tracker = get_tracker_fn()
    jobs = {}
    for job_name, state in tracker.items():
        jobs[job_name] = {
            "last_run": state.last_run_dt.isoformat() if state.last_run_dt else None,
            "consecutive_failures": state.consecutive_failures,
            "healthy": state.consecutive_failures == 0,
        }

    overall = "ok" if all(j["healthy"] for j in jobs.values()) else "degraded"
    return {"status": overall, "jobs": jobs}


def make_handler(get_tracker_fn: Callable) -> type:
    """Return a request handler class bound to the given tracker accessor."""

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ("/", "/health"):
                self.send_response(404)
                self.end_headers()
                return

            try:
                status = _build_status(get_tracker_fn)
                code = 200 if status["status"] == "ok" else 503
                body = json.dumps(status).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as exc:  # pragma: no cover
                logger.exception("healthcheck handler error: %s", exc)
                self.send_response(500)
                self.end_headers()

        def log_message(self, fmt, *args):  # silence default access log
            pass

    return HealthHandler


class HealthCheckServer:
    def __init__(self, host: str, port: int, get_tracker_fn: Callable):
        self.host = host
        self.port = port
        handler = make_handler(get_tracker_fn)
        self._server = HTTPServer((host, port), handler)
        self._thread: Optional[Thread] = None

    def start(self):
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info("healthcheck server listening on %s:%d", self.host, self.port)

    def stop(self):
        self._server.shutdown()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("healthcheck server stopped")
