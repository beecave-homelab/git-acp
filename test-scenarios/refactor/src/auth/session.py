"""Session refactor sample."""

from __future__ import annotations

def refactor_session_management(session: dict[str, str]) -> dict[str, str]:
    """Refactor session management by centralizing normalization."""
    return {key.strip(): value.strip() for key, value in session.items()}

def cleanup_session_flags(flags: list[str]) -> list[str]:
    """Clean up duplicate session flags without changing behavior."""
    return sorted(set(flags))
