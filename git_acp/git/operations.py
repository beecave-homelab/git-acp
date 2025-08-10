from .core import GitError, run_git_command
from .staging import (
    get_current_branch,
    git_add,
    git_commit,
    git_push,
    unstage_files,
    setup_signal_handlers,
)
from .diff import get_changed_files, get_diff
from .history import get_recent_commits, find_related_commits, analyze_commit_patterns
from .management import (
    create_branch,
    delete_branch,
    merge_branch,
    manage_remote,
    manage_tags,
    manage_stash,
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
