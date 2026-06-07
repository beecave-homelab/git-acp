"""Optimized index sample."""

from __future__ import annotations

class OptimizedIndex:
    """Optimize index lookup performance with a precomputed dictionary."""

    def __init__(self, values: list[str]) -> None:
        self._index = {value: position for position, value in enumerate(values)}

    def lookup(self, value: str) -> int | None:
        """Improve lookup speed for repeated reads."""
        return self._index.get(value)
