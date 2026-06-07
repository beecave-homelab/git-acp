"""API latency benchmark sample."""

from __future__ import annotations

def improve_api_latency_benchmark(samples: list[float]) -> float:
    """Improve API latency benchmark reporting by using a sorted median."""
    ordered = sorted(samples)
    if not ordered:
        return 0.0
    return ordered[len(ordered) // 2]
