"""Re-exports for git operations subpackage."""

from .core import GitError, run_git_command
from .diff import get_changed_files, get_diff
from .history import analyze_commit_patterns, find_related_commits, get_recent_commits
from .management import (
    create_branch,
    delete_branch,
    manage_remote,
    manage_stash,
    manage_tags,
    merge_branch,
)
from .staging import (
    get_current_branch,
    git_add,
    git_commit,
    git_push,
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
]
