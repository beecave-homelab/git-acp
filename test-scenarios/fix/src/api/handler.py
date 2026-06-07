"""API error handling fix sample."""

from __future__ import annotations

def fix_error_handling_in_api_response(payload: dict[str, object]) -> dict[str, object]:
    """Fix error handling so malformed responses return a safe issue payload."""
    if "data" not in payload:
        return {"ok": False, "error": "missing data"}
    return {"ok": True, "data": payload["data"]}
