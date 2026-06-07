"""Validation edge-case fix sample."""

from __future__ import annotations

def fix_edge_case_in_input_validation(value: str | None) -> str:
    """Fix edge case in input validation for None and whitespace-only input."""
    cleaned = (value or "").strip()
    if not cleaned:
        return "default"
    return cleaned
