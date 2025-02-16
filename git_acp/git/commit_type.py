"""Defines conventional commit types using an enumeration."""

from enum import Enum


class CommitType(Enum):
    """Enumeration of conventional commit types with their prefix values.

    Valid types:
    - FEAT: New feature
    - FIX: Bug fix
    - DOCS: Documentation changes
    - STYLE: Code style/formatting
    - REFACTOR: Code refactoring
    - TEST: Test-related changes
    - CHORE: Maintenance tasks
    - REVERT: Revert a previous commit
    """

    FEAT = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    TEST = "test"
    CHORE = "chore"
    REVERT = "revert"

    @classmethod
    def from_str(cls, value: str) -> "CommitType":
        """Convert a string to matching CommitType enum member.

        Args:
            value: String representation of commit type

        Returns:
            CommitType: Matching enum member

        Raises:
            ValueError: If no matching commit type found
        """
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Invalid commit type: {value}")
