"""Commit type classification module for git-acp package."""

from enum import Enum
from git_acp.git_operations import run_git_command, GitError

class CommitType(Enum):
    """Enum for commit types with their corresponding emojis."""
    FEAT = "feat ✨"
    FIX = "fix 🐛"
    DOCS = "docs 📝"
    STYLE = "style 💎"
    REFACTOR = "refactor ♻️"
    TEST = "test 🧪"
    CHORE = "chore 📦"
    REVERT = "revert ⏪"

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

    # First check for documentation changes
    doc_keywords = ["docs/", ".md", "readme", "documentation", "license"]
    if check_pattern(doc_keywords, diff):
        if config.verbose:
            print("[yellow]Debug: Classified as DOCS[/yellow]")
        return CommitType.DOCS

    # Then check for test changes
    test_keywords = ["test", ".test.", "_test", "test_"]
    if check_pattern(test_keywords, diff):
        if config.verbose:
            print("[yellow]Debug: Classified as TEST[/yellow]")
        return CommitType.TEST

    # Check for style changes
    style_keywords = ["style", "format", "whitespace", "lint", "prettier", "eslint"]
    if check_pattern(style_keywords, diff):
        if config.verbose:
            print("[yellow]Debug: Classified as STYLE[/yellow]")
        return CommitType.STYLE

    # Check for refactor
    refactor_keywords = ["refactor", "restructure", "cleanup", "clean up", "reorganize"]
    if check_pattern(refactor_keywords, diff):
        if config.verbose:
            print("[yellow]Debug: Classified as REFACTOR[/yellow]")
        return CommitType.REFACTOR

    # Check for bug fixes
    fix_keywords = ["fix", "bug", "patch", "issue", "error", "crash", "problem", "resolve"]
    if check_pattern(fix_keywords, diff):
        if config.verbose:
            print("[yellow]Debug: Classified as FIX[/yellow]")
        return CommitType.FIX

    # Check for reverts
    if "revert" in diff.lower():
        if config.verbose:
            print("[yellow]Debug: Classified as REVERT[/yellow]")
        return CommitType.REVERT

    # Check for features
    feature_keywords = ["add", "new", "feature", "update", "introduce", 
                       "implement", "enhance", "create", "improve", "support"]
    if check_pattern(feature_keywords, diff):
        if config.verbose:
            print("[yellow]Debug: Classified as FEAT[/yellow]")
        return CommitType.FEAT

    if config.verbose:
        print("[yellow]Debug: Defaulting to CHORE[/yellow]")
    return CommitType.CHORE 