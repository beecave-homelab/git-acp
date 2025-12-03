"""Compatibility layer for git operation helpers.

This module provides a stable import surface for git-related helpers by
re-exporting functions from the internal ``operations`` and related modules.
It also implements ``get_changed_files`` directly so that tests can patch the
``run_git_command`` symbol in this module and fully control its behavior.
"""

from git_acp.config import EXCLUDED_PATTERNS
from git_acp.utils import OptionalConfig, debug_header, debug_item

from .operations import (
    GitError,
    analyze_commit_patterns,
    create_branch,
    delete_branch,
    find_related_commits,
    get_current_branch,
    get_diff,
    get_recent_commits,
    git_add,
    git_commit,
    git_push,
    manage_remote,
    manage_stash,
    manage_tags,
    merge_branch,
    run_git_command,
    setup_signal_handlers,
    unstage_files,
)


def get_changed_files(
    config: OptionalConfig = None, staged_only: bool = False
) -> set[str]:
    """Get list of changed files.

    This mirrors :func:`git_acp.git.diff.get_changed_files` but is implemented
    here so that tests can patch :func:`run_git_command` via
    ``git_acp.git.git_operations``.

    Args:
        config: Optional configuration for verbose output.
        staged_only: If True, only return staged files.

    Returns:
        set[str]: Set of changed file paths.
    """
    files: set[str] = set()
    if config and config.verbose:
        debug_header(f"Getting {'staged ' if staged_only else ''}changed files")

    if staged_only:
        stdout_staged_only, _ = run_git_command(
            ["git", "diff", "--staged", "--name-only"], config
        )
        if config and config.verbose:
            debug_item("Raw git diff --staged --name-only output", stdout_staged_only)
        files = set(stdout_staged_only.splitlines())
    else:
        stdout_status, _ = run_git_command(
            ["git", "status", "--porcelain", "-uall"], config
        )
        if config and config.verbose:
            debug_item("Raw git status --porcelain -uall output", stdout_status)

        def process_status_line(line: str) -> str | None:
            if not line.strip():
                return None
            if config and config.verbose:
                debug_item("Processing status line", line)
            if " -> " in line:
                path = line.split(" -> ")[-1].strip()
            else:
                path = line[2:].lstrip()
            if config and config.verbose:
                debug_item("Extracted path from status", path)
            return path

        for line in stdout_status.splitlines():
            path = process_status_line(line)
            if path:
                files.add(path)

    if files:
        excluded_files = set()
        for f in files:
            for pattern in EXCLUDED_PATTERNS:
                if pattern in f:
                    if config and config.verbose:
                        debug_item(
                            "Excluding file based on pattern",
                            f"Pattern '{pattern}' matched '{f}'",
                        )
                    excluded_files.add(f)
                    break
        files -= excluded_files

    if config and config.verbose:
        debug_item("Final file set after exclusion", str(files))

    return files


__all__ = [
    "GitError",
    "run_git_command",
    "get_current_branch",
    "git_add",
    "git_commit",
    "git_push",
    "get_changed_files",
    "unstage_files",
    "get_diff",
    "get_recent_commits",
    "find_related_commits",
    "analyze_commit_patterns",
    "create_branch",
    "delete_branch",
    "merge_branch",
    "manage_remote",
    "manage_tags",
    "manage_stash",
    "setup_signal_handlers",
    "EXCLUDED_PATTERNS",
]
