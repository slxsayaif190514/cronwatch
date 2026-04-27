"""Alert sending logic — supports email and webhook channels."""

import json
import logging
import smtplib
import urllib.request
from email.mime.text import MIMEText
from typing import Optional

from cronwatch.config import AlertConfig

logger = logging.getLogger(__name__)


def send_alert(config: AlertConfig, subject: str, body: str) -> bool:
    """Dispatch alert via configured channels. Returns True if at least one succeeded."""
    success = False
    if config.email:
        if _send_email(config, subject, body):
            success = True
    if config.webhook_url:
        if _send_webhook(config.webhook_url, subject, body):
            success = True
    return success


def _send_email(config: AlertConfig, subject: str, body: str) -> bool:
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = config.email_from or "cronwatch@localhost"
        msg["To"] = config.email

        smtp_host = config.smtp_host or "localhost"
        smtp_port = config.smtp_port or 25

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if config.smtp_user and config.smtp_password:
                server.login(config.smtp_user, config.smtp_password)
            server.sendmail(msg["From"], [config.email], msg.as_string())

        logger.info("Email alert sent to %s", config.email)
        return True
    except Exception as exc:
        logger.error("Failed to send email alert: %s", exc)
        return False


def _send_webhook(url: str, subject: str, body: str) -> bool:
    try:
        payload = json.dumps({"subject": subject, "body": body}).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info("Webhook alert sent, status %s", resp.status)
        return True
    except Exception as exc:
        logger.error("Failed to send webhook alert: %s", exc)
        return False


def build_overdue_message(job_name: str, minutes_overdue: float) -> tuple[str, str]:
    subject = f"[cronwatch] Job '{job_name}' is overdue"
    body = (
        f"The cron job '{job_name}' has not run as expected.\n"
        f"It is approximately {minutes_overdue:.1f} minute(s) past its scheduled time.\n"
        "Please investigate."
    )
    return subject, body


def build_failure_message(job_name: str, consecutive: int) -> tuple[str, str]:
    subject = f"[cronwatch] Job '{job_name}' failed"
    body = (
        f"The cron job '{job_name}' has reported a failure.\n"
        f"Consecutive failures: {consecutive}\n"
        "Please investigate."
    )
    return subject, body
