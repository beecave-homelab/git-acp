"""Helper refactor sample."""

from __future__ import annotations

def simplify_helper_functions(values: list[str]) -> list[str]:
    """Simplify helper functions and clean up repeated string handling."""
    return [value.strip().lower() for value in values if value.strip()]
