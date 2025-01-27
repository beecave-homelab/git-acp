"""Git operations package for git-acp."""

from git_acp.git.git_operations import (
    GitError,
    run_git_command,
    get_current_branch,
    git_add,
    git_commit,
    git_push,
    get_changed_files,
    unstage_files,
    get_diff,
    get_recent_commits,
    find_related_commits,
    analyze_commit_patterns
)
from git_acp.git.classification import CommitType, classify_commit_type

__all__ = [
    'GitError',
    'run_git_command',
    'get_current_branch',
    'git_add',
    'git_commit',
    'git_push',
    'get_changed_files',
    'unstage_files',
    'get_diff',
    'get_recent_commits',
    'find_related_commits',
    'analyze_commit_patterns',
    'CommitType',
    'classify_commit_type'
]
