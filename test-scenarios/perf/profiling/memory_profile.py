"""Memory profiling sample."""

from __future__ import annotations

def reduce_memory_usage_in_hot_path(values: list[str]) -> tuple[str, ...]:
    """Reduce memory usage in hot path by returning an immutable tuple."""
    return tuple(value.strip() for value in values if value.strip())
