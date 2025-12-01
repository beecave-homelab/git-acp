"""Compatibility layer for git operation helpers."""

from git_acp.config import EXCLUDED_PATTERNS

from .operations import (
    GitError,
    analyze_commit_patterns,
    create_branch,
    delete_branch,
    find_related_commits,
    get_changed_files,
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
