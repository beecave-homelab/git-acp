"""Route handler refactor sample."""

from __future__ import annotations

def refactor_api_route_handlers(method: str, path: str) -> str:
    """Refactor API route handlers by extracting route key construction."""
    return f"{method.upper()} {path.rstrip('/')}"
