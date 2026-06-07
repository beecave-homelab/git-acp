"""User profile feature sample for classifier validation."""

from __future__ import annotations

class UserProfileService:
    """Add support for editable user profiles and display preferences."""

    def create_profile(self, user_id: str, display_name: str) -> dict[str, str]:
        """Create a profile record for a new account feature."""
        return {"user_id": user_id, "display_name": display_name, "visibility": "private"}

    def update_preferences(self, profile: dict[str, str], theme: str) -> dict[str, str]:
        """Enable theme preference updates for the profile page."""
        profile["theme"] = theme
        return profile
