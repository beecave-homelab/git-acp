"""Database connection regression fix sample."""

from __future__ import annotations

def fix_connection_pool_regression(active: int, limit: int) -> bool:
    """Fix connection pool regression by refusing overflow allocations."""
    if limit <= 0:
        return False
    return active < limit

def resolve_idle_connection_count(count: int) -> int:
    """Resolve negative idle counts reported by older drivers."""
    return max(count, 0)
