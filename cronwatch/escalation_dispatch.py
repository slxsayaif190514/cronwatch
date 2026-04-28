"""High-level helper that combines EscalationStore with the notifier to dispatch
alerts to the primary channel and, once the threshold is hit, also to the
escalation channel."""

from __future__ import annotations

from typing import Optional

from cronwatch.escalation import EscalationStore
from cronwatch.notifier import dispatch


def alert_with_escalation(
    store: EscalationStore,
    job_name: str,
    subject: str,
    body: str,
    primary_channel: str = "noop",
    escalation_channel: Optional[str] = None,
    escalation_threshold: int = 3,
) -> dict:
    """Send an alert and escalate if the threshold has been reached.

    Returns a dict with keys ``count``, ``escalated``, and ``channels_used``.
    """
    count = store.record_alert(job_name)
    channels_used = [primary_channel]

    dispatch(primary_channel, subject=subject, body=body, job=job_name)

    escalated = False
    if (
        escalation_channel
        and escalation_channel != primary_channel
        and store.should_escalate(job_name, escalation_threshold)
    ):
        escalated_subject = f"[ESCALATED x{count}] {subject}"
        dispatch(escalation_channel, subject=escalated_subject, body=body, job=job_name)
        channels_used.append(escalation_channel)
        escalated = True

    return {"count": count, "escalated": escalated, "channels_used": channels_used}


def resolve_job(
    store: EscalationStore,
    job_name: str,
    notify_channel: Optional[str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
) -> None:
    """Reset escalation state and optionally send a recovery notification."""
    store.reset(job_name)
    if notify_channel and subject:
        dispatch(notify_channel, subject=subject, body=body or "", job=job_name)
