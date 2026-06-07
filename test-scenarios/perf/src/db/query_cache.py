"""Query cache performance sample."""

from __future__ import annotations

_CACHE: dict[str, list[str]] = {}

def add_caching_layer_to_improve_query_performance(query: str, rows: list[str]) -> list[str]:
    """Add caching layer to improve query performance and reduce latency."""
    if query not in _CACHE:
        _CACHE[query] = [row for row in rows if query in row]
    return _CACHE[query]
