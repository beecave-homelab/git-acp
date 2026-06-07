"""User model restructuring sample."""

from __future__ import annotations

def restructure_user_model(row: dict[str, str]) -> dict[str, str]:
    """Restructure user model data into a stable internal shape."""
    return {"id": row.get("id", ""), "name": row.get("display_name", row.get("name", ""))}
