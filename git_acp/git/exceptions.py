"""Git-related exceptions."""

from typing import Optional


class GitError(Exception):
    """Custom exception for git-related errors.

    Attributes:
        message: The error message
        suggestion: Optional suggestion for fixing the error
        context: Optional context about where/why the error occurred
    """

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        context: Optional[str] = None,
    ):
        self.message = message
        self.suggestion = suggestion
        self.context = context

        # Build the full error message
        parts = []

        # Add context and message
        if context:
            parts.append(f"{context}:")
        parts.append(message)

        # Add suggestion if provided, combining multiple suggestions with semicolons
        if suggestion:
            suggestions = suggestion.split("\n")
            formatted_suggestions = "; ".join(
                s.strip() for s in suggestions if s.strip()
            )
            if formatted_suggestions:
                parts.append(f"\nSuggestion: {formatted_suggestions}")

        # Join all parts
        super().__init__("\n".join(parts))
