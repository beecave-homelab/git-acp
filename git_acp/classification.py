"""Commit type classification module for git-acp package."""

from enum import Enum
from git_acp.git_operations import run_git_command, GitError
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

def get_git_diff(config) -> str:
    """Get the git diff, checking both staged and unstaged changes."""
    # First try to get staged changes
    stdout, _ = run_git_command(["git", "diff", "--staged"])
    if stdout.strip():
        if config.verbose:
            print("[yellow]Debug: Using staged changes diff[/yellow]")
        return stdout
    # If no staged changes, get unstaged changes
    if config.verbose:
        print("[yellow]Debug: No staged changes, using unstaged diff[/yellow]")
    stdout, _ = run_git_command(["git", "diff"])
    return stdout

def classify_commit_type(config) -> CommitType:
    """
    Classify the commit type based on the git diff content.
    
    Args:
        config: GitConfig instance containing configuration options
        
    Returns:
        CommitType: The classified commit type
    """
    diff = get_git_diff(config)
    
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