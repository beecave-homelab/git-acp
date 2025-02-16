"""
Package for commit message generation functionality.
"""

from git_acp.commit.commit import git_add, git_commit, git_push
from git_acp.commit.builder import (
    build_advanced_commit_message,
    build_simple_commit_message,
)
from git_acp.commit.prompt_builder import (
    create_advanced_commit_message_prompt,
    create_simple_commit_message_prompt,
)
from git_acp.commit.generation import (
    get_commit_context,
    edit_commit_message,
    generate_commit_message,
)

__all__ = [
    "git_add",
    "git_commit",
    "git_push",
    "build_advanced_commit_message",
    "build_simple_commit_message",
    "create_advanced_commit_message_prompt",
    "create_simple_commit_message_prompt",
    "get_commit_context",
    "edit_commit_message",
    "generate_commit_message",
]
