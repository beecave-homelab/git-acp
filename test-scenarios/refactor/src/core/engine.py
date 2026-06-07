"""Engine refactor sample."""

from __future__ import annotations

def consolidate_engine_logic(steps: list[str]) -> list[str]:
    """Consolidate engine logic and remove dead code paths from execution."""
    return [step for step in steps if step != "deprecated"]
