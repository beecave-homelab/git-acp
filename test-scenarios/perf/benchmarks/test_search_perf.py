"""Search performance benchmark sample."""

from __future__ import annotations

def optimize_search_query_performance(items: list[str], query: str) -> list[str]:
    """Optimize search query performance by pre-normalizing the query."""
    needle = query.casefold()
    return [item for item in items if needle in item.casefold()]

def benchmark_search_latency() -> int:
    """Benchmark search latency for repeated query execution."""
    return len(optimize_search_query_performance(["alpha", "beta"], "a"))
