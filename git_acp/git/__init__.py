"""Git operations package for git-acp."""

from git_acp.git.exceptions import GitError
from git_acp.git.core import run_git_command
from git_acp.git.runner import setup_signal_handlers
from git_acp.git.status import (
    get_changed_files,
    unstage_files,
    get_name_status_changes,
    analyze_diff_hotspots,
)
from git_acp.git.history import (
    get_recent_commits,
    find_related_commits,
    get_diff,
    analyze_commit_patterns,
    get_commit_messages,
    get_diff_between_branches,
    analyze_commit_types,
)
from git_acp.git.branch import (
    get_current_branch,
    get_default_branch,
    create_branch,
    delete_branch,
    merge_branch,
    get_branch_age,
    find_parent_branch,
)
from git_acp.git.commit_type import CommitType
from git_acp.git.classification import classify_commit_type
from git_acp.git.stash import (
    stash_changes,
    pop_stash,
    list_stashes,
    clear_stashes,
)
from git_acp.git.tag import (
    create_tag,
    delete_tag,
    list_tags,
)
from git_acp.git.remote import (
    add_remote,
    remove_remote,
    get_remote_url,
)

# Re-export commit operations
from git_acp.commit.commit import git_add, git_commit, git_push

__all__ = [
    "GitError",
    "run_git_command",
    "get_current_branch",
    "get_default_branch",
    "create_branch",
    "delete_branch",
    "merge_branch",
    "get_branch_age",
    "find_parent_branch",
    "git_add",
    "git_commit",
    "git_push",
    "get_changed_files",
    "unstage_files",
    "get_name_status_changes",
    "analyze_diff_hotspots",
    "get_diff",
    "get_recent_commits",
    "find_related_commits",
    "analyze_commit_patterns",
    "get_commit_messages",
    "get_diff_between_branches",
    "analyze_commit_types",
    "CommitType",
    "classify_commit_type",
    "setup_signal_handlers",
    "stash_changes",
    "pop_stash",
    "list_stashes",
    "clear_stashes",
    "create_tag",
    "delete_tag",
    "list_tags",
    "add_remote",
    "remove_remote",
    "get_remote_url",
]
