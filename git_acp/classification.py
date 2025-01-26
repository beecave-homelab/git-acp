"""Commit type classification module for git-acp package."""

from enum import Enum
from git_acp.git_operations import run_git_command, GitError, get_diff
from git_acp.constants import COMMIT_TYPE_PATTERNS, COMMIT_TYPES

class CommitType(Enum):
    """Enum for commit types with their corresponding emojis."""
    FEAT = COMMIT_TYPES['FEAT']
    FIX = COMMIT_TYPES['FIX']
    DOCS = COMMIT_TYPES['DOCS']
    STYLE = COMMIT_TYPES['STYLE']
    REFACTOR = COMMIT_TYPES['REFACTOR']
    TEST = COMMIT_TYPES['TEST']
    CHORE = COMMIT_TYPES['CHORE']
    REVERT = COMMIT_TYPES['REVERT']

    @classmethod
    def from_str(cls, type_str: str) -> 'CommitType':
        """Convert string to CommitType, case insensitive."""
        try:
            return cls[type_str.upper()]
        except KeyError:
            valid_types = [t.name.lower() for t in cls]
            raise GitError(
                f"Invalid commit type: {type_str}. "
                f"Valid types are: {', '.join(valid_types)}"
            )

def get_changes() -> str:
    """Get the changes to be committed.
    
    Returns:
        str: The changes as a diff string
        
    Raises:
        GitError: If unable to get changes
    """
    try:
        # First try staged changes
        diff = get_diff("staged")
        if not diff:
            # If no staged changes, get unstaged changes
            diff = get_diff("unstaged")
        return diff
    except GitError as e:
        raise GitError(f"Failed to get changes: {e}") from e

def classify_commit_type(config) -> CommitType:
    """
    Classify the commit type based on the git diff content.
    
    Args:
        config: GitConfig instance containing configuration options
        
    Returns:
        CommitType: The classified commit type
    """
    diff = get_changes()
    
    def check_pattern(keywords: list[str], diff_text: str) -> bool:
        """Check if any of the keywords appear in the diff text."""
        matches = [k for k in keywords if k in diff_text.lower()]
        if matches and config.verbose:
            print(f"[yellow]Debug: Matched keywords: {matches}[/yellow]")
        return bool(matches)

    # Use patterns from constants
    for commit_type, keywords in COMMIT_TYPE_PATTERNS.items():
        if check_pattern(keywords, diff):
            if config.verbose:
                print(f"[yellow]Debug: Classified as {commit_type.upper()}[/yellow]")
            return CommitType[commit_type.upper()]

    if config.verbose:
        print("[yellow]Debug: Defaulting to CHORE[/yellow]")
    return CommitType.CHORE 