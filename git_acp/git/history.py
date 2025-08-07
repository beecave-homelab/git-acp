"""Commit history and analysis utilities."""

from collections import Counter
import json
from typing import Dict, List, TYPE_CHECKING

from git_acp.config import DEFAULT_NUM_RECENT_COMMITS
from git_acp.utils import OptionalConfig, debug_header, debug_item, debug_json

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from git_acp.git.git_operations import GitError


def get_recent_commits(
    num_commits: int = DEFAULT_NUM_RECENT_COMMITS,
    config: OptionalConfig = None,
) -> List[Dict[str, str]]:
    """Get recent commit history.

    Args:
        num_commits (int): Number of commits to retrieve.
        config (OptionalConfig | None): Optional configuration settings.

    Returns:
        List[Dict[str, str]]: Recent commit information.

    Raises:
        GitError: If the git command fails.
    """
    from git_acp.git.git_operations import GitError, run_git_command

    try:
        if config and config.verbose:
            debug_header("Getting recent commits")
            debug_item("Number of commits", str(num_commits))

        format_str = (
            '--pretty=format:{"hash":"%h","message":"%s",'
            '"author":"%an","date":"%ad"}'
        )
        stdout, _ = run_git_command(
            [
                "git",
                "log",
                f"-{num_commits}",
                format_str,
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
) -> List[Dict[str, str]]:
    """Find commits related to the current changes.

    Args:
        diff_content (str): Diff content to compare.
        num_commits (int): Number of commits to return.
        config (OptionalConfig | None): Optional configuration settings.

    Returns:
        List[Dict[str, str]]: Related commit information.

    Raises:
        GitError: If the git command fails.
    """
    from git_acp.git.git_operations import GitError, run_git_command

    try:
        all_commits = get_recent_commits(num_commits * 2, config)
        related_commits = []

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
    commits: List[Dict[str, str]],
    config: OptionalConfig = None,
) -> Dict[str, Dict[str, int]]:
    """Analyze commit history to find patterns in commit types and scopes.

    Args:
        commits (List[Dict[str, str]]): Commit dictionaries to analyze.
        config (OptionalConfig | None): Optional configuration settings.

    Returns:
        Dict[str, Dict[str, int]]: Counts of commit types and scopes.
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


__all__ = [
    "get_recent_commits",
    "find_related_commits",
    "analyze_commit_patterns",
]
