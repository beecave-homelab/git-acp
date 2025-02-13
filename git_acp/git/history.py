"""Git history and diff operations."""

from typing import List, Optional, Dict, Union
from collections import Counter

from git_acp.git.exceptions import GitError
from git_acp.git.core import run_git_command
from git_acp.utils.types import GitConfig


def get_recent_commits(
    num_commits: int = 3, config: Optional[GitConfig] = None
) -> List[str]:
    """Get recent commit messages.

    Args:
        num_commits: Number of recent commits to fetch
        config: Optional configuration

    Returns:
        List of recent commit messages
    """
    try:
        stdout, _ = run_git_command(
            ["git", "log", f"-{num_commits}", "--oneline"], config
        )
        return stdout.split("\n") if stdout else []
    except GitError:
        return []


def find_related_commits(
    files: List[str], num_commits: int = 3, config: Optional[GitConfig] = None
) -> List[str]:
    """Find commits related to the given files.

    Args:
        files: List of file paths
        num_commits: Maximum number of commits to return
        config: Optional configuration

    Returns:
        List of related commit messages
    """
    try:
        commits = []
        for file in files:
            stdout, _ = run_git_command(
                ["git", "log", f"-{num_commits}", "--oneline", "--", file], config
            )
            if stdout:
                commits.extend(stdout.split("\n"))
        return list(dict.fromkeys(commits))[:num_commits]  # Remove duplicates
    except GitError:
        return []


def get_diff(
    diff_type: Union[str, bool] = False, config: Optional[GitConfig] = None
) -> str:
    """Get the diff of changes.

    Args:
        diff_type: Either a boolean for staged_only, or a string 'staged'/'unstaged'
        config: Optional configuration

    Returns:
        Diff output as string
    """
    try:
        cmd = ["git", "diff"]

        # Handle both boolean and string inputs
        if isinstance(diff_type, str):
            if diff_type.lower() == "staged":
                cmd.append("--staged")
        elif diff_type:  # boolean True
            cmd.append("--staged")

        stdout, _ = run_git_command(cmd, config)
        return stdout
    except GitError:
        return ""


def analyze_commit_patterns(
    num_commits: int = 10, config: Optional[GitConfig] = None
) -> Dict[str, Dict[str, int]]:
    """Analyze patterns in recent commit messages.

    Args:
        num_commits: Number of commits to analyze
        config: Optional configuration

    Returns:
        Dictionary containing pattern frequencies with 'types' key
    """
    try:
        stdout, _ = run_git_command(
            ["git", "log", f"-{num_commits}", "--oneline"], config
        )
        commits = stdout.split("\n") if stdout else []
        patterns = {}

        for commit in commits:
            words = commit.split()[1:]  # Skip commit hash
            for word in words:
                if len(word) > 3:  # Skip short words
                    patterns[word.lower()] = patterns.get(word.lower(), 0) + 1

        return {
            "types": dict(
                sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:5]
            )
        }
    except GitError:
        return {"types": {}}


def get_commit_messages(
    target: str, source: str, config: Optional[GitConfig] = None
) -> dict:
    """Get commit messages between two branches.

    Args:
        target: Target branch name
        source: Source branch name
        config: Optional configuration

    Returns:
        Dictionary containing:
            - messages: List of clean commit messages for title generation
            - messages_with_details: List of detailed commit messages including body

    Raises:
        GitError: If getting commit messages fails
    """
    try:
        # First get just the messages for title generation
        output, _ = run_git_command(
            [
                "git",
                "log",
                "--pretty=format:%s",  # Subject line only
                "--no-merges",
                f"{target}...{source}",
            ],
            config,
        )

        # Clean up the messages for title generation
        messages = []
        # Split on newlines since we only have subject lines
        for msg in output.splitlines():
            if msg.strip():
                # Remove any conventional commit prefixes
                if ": " in msg:
                    msg = msg.split(": ", 1)[1]
                messages.append(msg)

        # Then get the full format for display, including commit body
        output_with_details, _ = run_git_command(
            [
                "git",
                "log",
                "--pretty=format:%h - %B",  # Full format with hash and full message
                "--no-merges",
                f"{target}...{source}",
            ],
            config,
        )

        messages_with_details = []
        current_message = []

        # Process the detailed output to handle multi-line commit messages
        for line in output_with_details.split("\n"):
            if line.startswith(tuple("0123456789abcdef")):  # New commit starts
                if current_message:  # Save previous message if exists
                    messages_with_details.append("\n".join(current_message))
                current_message = [line.strip()]
            elif line.strip():  # Add non-empty lines to current message
                current_message.append(line.strip())

        # Add the last message
        if current_message:
            messages_with_details.append("\n".join(current_message))

        # Store both versions
        return {
            "messages": messages,  # Clean messages for title generation
            "messages_with_details": messages_with_details,  # Detailed messages
        }
    except Exception as e:
        raise GitError(f"Failed to get commit messages: {str(e)}") from e


def get_diff_between_branches(target: str, source: str) -> str:
    """Get diff between two branches.

    Args:
        target: Target branch name
        source: Source branch name

    Returns:
        Diff text

    Raises:
        GitError: If getting diff fails
    """
    try:
        stdout, _ = run_git_command(
            ["git", "--no-pager", "diff", f"{target}...{source}"]
        )
        return stdout
    except Exception as e:
        raise GitError(f"Failed to get diff between branches: {str(e)}") from e


def analyze_commit_types(messages: List[str]) -> Dict[str, int]:
    """Analyze commit messages for conventional commit type distribution.

    Args:
        messages: List of commit messages

    Returns:
        Dictionary with commit types and their counts
    """

    types = Counter()

    for msg in messages:
        if ":" in msg:
            commit_type = msg.split(":", 1)[0].lower().strip()
            if commit_type:
                types[commit_type] += 1
        else:
            types["other"] += 1

    return dict(types)
