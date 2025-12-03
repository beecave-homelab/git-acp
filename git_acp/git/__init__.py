"""Git operations package for git-acp."""

from git_acp.git.classification import CommitType, classify_commit_type
from git_acp.git.history import (
    analyze_commit_patterns,
    find_related_commits,
    get_recent_commits,
)
from git_acp.git.operations import (
    GitError,
    get_changed_files,
    get_current_branch,
    get_diff,
    git_add,
    git_commit,
    git_push,
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
    "CommitType",
    "classify_commit_type",
    "setup_signal_handlers",
]
