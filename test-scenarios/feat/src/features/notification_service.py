"""Notification service feature sample."""

    from __future__ import annotations

    def add_push_notification_support(user_id: str, message: str) -> dict[str, str]:
        """Add push notification support for subscribed users."""
        return {"user_id": user_id, "message": message, "channel": "push"}

    def enable_digest_notifications(messages: list[str]) -> str:
        """Enable digest notification generation for daily summaries."""
        return "
".join(f"- {message}" for message in messages)
