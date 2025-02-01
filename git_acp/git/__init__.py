"""Git operations package for git-acp."""

from git_acp.git.runner import run_git_command, GitError, setup_signal_handlers
from git_acp.git.commit import git_add, git_commit, git_push
from git_acp.git.status import get_changed_files, unstage_files
from git_acp.git.history import get_recent_commits, find_related_commits, get_diff, analyze_commit_patterns
from git_acp.git.branch import get_current_branch
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
    'classify_commit_type',
    'setup_signal_handlers'
]
