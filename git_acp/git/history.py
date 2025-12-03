"""Git history and commit analysis operations."""

from __future__ import annotations

import json
from collections import Counter

from git_acp.config import DEFAULT_NUM_RECENT_COMMITS
from git_acp.utils import OptionalConfig, debug_header, debug_item, debug_json

from .core import GitError, run_git_command


def get_recent_commits(
    num_commits: int = DEFAULT_NUM_RECENT_COMMITS, config: OptionalConfig = None
) -> list[dict[str, str]]:
    """Get recent commit history.

    Args:
        num_commits: Number of recent commits to retrieve.
        config: Optional configuration for verbose output.

    Returns:
        list[dict[str, str]]: List of commit dictionaries with hash, message, etc.

    Raises:
        GitError: If the git log command fails.
    """
    try:
        if config and config.verbose:
            debug_header("Getting recent commits")
            debug_item("Number of commits", str(num_commits))

        stdout, _ = run_git_command(
            [
                "git",
                "log",
                f"-{num_commits}",
                '--pretty=format:{"hash":"%h","message":"%s","author":"%an","date":"%ad"}',
                "--date=short",
            ],
            config,
        )

        if not stdout:
            return []

        commits = []
        for line in stdout.splitlines():
            try:
                commit = json.loads(line)
                commits.append(commit)
            except json.JSONDecodeError:
                continue

        if config and config.verbose:
            debug_item("Found commits", str(len(commits)))

        return commits

    except GitError as e:
        raise GitError(f"Failed to get recent commits: {str(e)}") from e


def find_related_commits(
    diff_content: str,
    num_commits: int = DEFAULT_NUM_RECENT_COMMITS,
    config: OptionalConfig = None,
) -> list[dict[str, str]]:
    """Find commits related to the current changes.

    Args:
        diff_content: The diff content to analyze for related files.
        num_commits: Maximum number of related commits to return.
        config: Optional configuration for verbose output.

    Returns:
        list[dict[str, str]]: List of related commit dictionaries.

    Raises:
        GitError: If unable to find related commits.
    """
    try:
        all_commits = get_recent_commits(num_commits * 2, config)
        related_commits: list[dict[str, str]] = []

        current_files = set()
        for line in diff_content.splitlines():
            if line.startswith("+++ b/") or line.startswith("--- a/"):
                file_path = line[6:]
                if file_path != "/dev/null":
                    current_files.add(file_path)

        for commit in all_commits:
            try:
                stdout, _ = run_git_command(
                    [
                        "git",
                        "show",
                        "--name-only",
                        "--pretty=format:",
                        commit["hash"],
                    ],
                    config,
                )

                commit_files = set(stdout.splitlines())
                if current_files & commit_files:
                    related_commits.append(commit)
                    if len(related_commits) >= num_commits:
                        break

            except GitError:
                continue

        if config and config.verbose:
            debug_header("Related commits found:")
            for commit in related_commits:
                debug_json(commit)

        return related_commits

    except GitError as e:
        raise GitError(f"Failed to find related commits: {str(e)}") from e


def analyze_commit_patterns(
    commits: list[dict[str, str]], config: OptionalConfig = None
) -> dict[str, dict[str, int]]:
    """Analyze commit history to find patterns in commit types and scopes.

    Args:
        commits: List of commit dictionaries to analyze.
        config: Optional configuration for verbose output.

    Returns:
        dict[str, dict[str, int]]: Dictionary with 'types' and 'scopes' counters.
    """
    if config and config.verbose:
        debug_header("Analyzing commit patterns")
        debug_item("Number of commits", str(len(commits)))

    patterns = {
        "types": Counter(),
        "scopes": Counter(),
    }

    for commit in commits:
        message = commit.get("message", "")
        if not message:
            continue

        if ":" in message:
            type_part = message.split(":", 1)[0].strip()
            if "(" in type_part:
                type_part = type_part.split("(", 1)[0].strip()
            type_part = type_part.split(" ", 1)[0].strip()
            patterns["types"][type_part.lower()] += 1

            if config and config.verbose:
                debug_item("Found commit type", type_part)

        if "(" in message and ")" in message:
            scope = message[message.find("(") + 1 : message.find(")")].strip()
            if scope:
                patterns["scopes"][scope.lower()] += 1
                if config and config.verbose:
                    debug_item("Found commit scope", scope)

    if config and config.verbose:
        debug_item("Commit types found", str(dict(patterns["types"])))
        debug_item("Commit scopes found", str(dict(patterns["scopes"])))

    return patterns
