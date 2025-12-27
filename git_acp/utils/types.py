"""Type definitions and aliases for git-acp package.

This module defines custom types and type aliases used throughout the package,
including configuration types, git operation types, and AI-related types.
"""

from dataclasses import dataclass
from typing import Any, Literal


# Configuration type
@dataclass
class GitConfig:
    """Configuration settings for git operations.

    Attributes:
        files: Files to be added to git staging. Defaults to "." for all files.
        message: Commit message to use. Defaults to "Automated commit".
        branch: Target branch for push operation. If None, uses current branch.
        use_ollama: Whether to use Ollama AI for commit message generation.
        interactive: Whether to allow editing of AI-generated commit messages.
        skip_confirmation: Whether to skip confirmation prompts.
        verbose: Whether to show debug information.
        prompt_type: Type of prompt to use for AI commit message generation.
        prompt: Optional custom prompt override for AI generation.
        ai_model: Optional AI model override for the current run.
        context_window: Optional context window size override in tokens.
        dry_run: Whether to run in dry-run mode without committing or pushing.
        auto_group: Whether to automatically group changes into multiple commits.
    """

    files: str = "."
    message: str = "Automated commit"
    branch: str | None = None
    use_ollama: bool = False
    interactive: bool = False
    skip_confirmation: bool = False
    verbose: bool = False
    prompt_type: str = "advanced"  # Default to advanced prompt type
    prompt: str | None = None
    ai_model: str | None = None
    context_window: int | None = None
    dry_run: bool = False
    auto_group: bool = False


# Git operations types
CommitDict = dict[str, str]
DiffType = Literal["staged", "unstaged"]
RemoteOperation = Literal["add", "remove", "set-url"]
TagOperation = Literal["create", "delete", "push"]
StashOperation = Literal["save", "pop", "apply", "drop", "list"]

# AI types
PromptType = Literal["simple", "advanced"]
Message = dict[str, str]
CommitContext = dict[str, Any]

# Common type aliases
OptionalConfig = GitConfig | None
