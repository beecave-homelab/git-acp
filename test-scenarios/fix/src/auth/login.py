"""Login bug fix sample."""

from __future__ import annotations

def fix_login_session_timeout_bug(now: int, expires_at: int | None) -> bool:
    """Fix login session timeout bug when expiry is missing."""
    if expires_at is None:
        return False
    return now < expires_at

def prevent_empty_session_token(token: str | None) -> str:
    """Prevent breaking authentication when a token is blank."""
    return token.strip() if token else "anonymous"
