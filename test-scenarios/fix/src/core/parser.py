"""Parser exception fix sample."""

from __future__ import annotations

def fix_exception_in_parser_for_malformed_input(raw: str) -> dict[str, str]:
    """Fix exception in parser for malformed input without separators."""
    if ":" not in raw:
        return {"key": "unknown", "value": raw}
    key, value = raw.split(":", 1)
    return {"key": key.strip(), "value": value.strip()}
