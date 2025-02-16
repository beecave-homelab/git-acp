"""Commit type classification and change analysis utilities.

This module provides functionality for classifying commit types and analyzing
changes in the repository to suggest appropriate commit types.
"""

from git_acp.git.exceptions import GitError
from git_acp.git.history import get_diff
from git_acp.config import COMMIT_TYPE_PATTERNS
from git_acp.utils import debug_header, debug_item
from git_acp.git.commit_type import CommitType


def get_changes() -> str:
    """Retrieve the staged or unstaged changes in the repository.

    Returns:
        str: The changes as a diff string

    Raises:
        GitError: If unable to get changes or if no changes are found
    """
    try:
        # First try staged changes
        diff = get_diff("staged")
        if not diff:
            # If no staged changes, get unstaged changes
            diff = get_diff("unstaged")

        if not diff:
            raise GitError(
                "No changes detected in the repository."
                "Please make some changes first."
            )

        return diff
    except GitError as e:
        raise GitError(
            "Failed to retrieve changes."
            "Please ensure you have a valid Git repository with changes."
        ) from e


def classify_commit_type(config) -> CommitType:
    """
    Classify the commit type based on the git diff content.

    Args:
        config: GitConfig instance containing configuration options

    Returns:
        CommitType: The classified commit type

    Raises:
        GitError: If unable to classify commit type or if changes cannot be retrieved
    """
    try:
        if config.verbose or config.ai_config.verbose:  # Check both verbose flags
            debug_header("Starting Commit Classification")
        diff = get_changes()

        def check_pattern(keywords: list[str], diff_text: str) -> bool:
            """Check if any of the keywords appear in the diff text."""
            try:
                matches = [k for k in keywords if k in diff_text.lower()]
                if matches and config.verbose:
                    debug_item(config, "Matched Keywords", ", ".join(matches))
                return bool(matches)
            except AttributeError as e:
                if config.verbose:
                    debug_header("Pattern Matching Error")
                    debug_item(config, "Error Type", e.__class__.__name__)
                    debug_item(config, "Error Message", str(e))
                return False

        # Use patterns from constants
        for commit_type, keywords in COMMIT_TYPE_PATTERNS.items():
            try:
                if check_pattern(keywords, diff):
                    if config.verbose:
                        debug_header("Commit Classification Result")
                        debug_item(config, "Selected Type", commit_type.upper())
                    return CommitType[commit_type.upper()]
            except KeyError as e:
                if config.verbose:
                    debug_header("Invalid Commit Type")
                    debug_item(config, "Type", commit_type)
                    debug_item(config, "Error", str(e))
                raise GitError(
                    f"Invalid commit type pattern detected: {commit_type}."
                    "Please check commit type definitions."
                ) from e

        if config.verbose:
            debug_header("No Specific Pattern Matched")
            debug_item(config, "Default Type", "CHORE")
        return CommitType.CHORE

    except GitError as e:
        if config.verbose:
            debug_header("Commit Classification Failed")
            debug_item(config, "Error Type", "GitError")
            debug_item(config, "Error Message", str(e))
        raise GitError(f"Failed to classify commit type: {str(e)}") from e
    except Exception as e:
        if config.verbose:
            debug_header("Unexpected Classification Error")
            debug_item(config, "Error Type", e.__class__.__name__)
            debug_item(config, "Error Message", str(e))
        raise GitError(
            "An unexpected error occurred during commit classification."
        ) from e
