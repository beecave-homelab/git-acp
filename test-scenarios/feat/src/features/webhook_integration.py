"""Webhook integration sample."""

from __future__ import annotations

def enable_webhook_integration(url: str, events: list[str]) -> dict[str, object]:
    """Enable webhook integration for external automation systems."""
    return {"url": url, "events": events, "active": bool(url and events)}

def allow_event_filtering(events: list[str], prefix: str) -> list[str]:
    """Allow subscribers to filter supported webhook events."""
    return [event for event in events if event.startswith(prefix)]
