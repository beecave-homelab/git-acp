"""Type definitions and aliases for git-acp package.

This module defines custom types and type aliases used throughout the package,
including configuration types, git operation types, and AI-related types.
"""

from typing import Dict, Optional, Any, Literal
from dataclasses import dataclass


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
    """

    files: str = "."
    message: str = "Automated commit"
    branch: Optional["GitConfig"] = None
    use_ollama: bool = False
    interactive: bool = False
    skip_confirmation: bool = False
    verbose: bool = False
    prompt_type: str = "advanced"  # Default to advanced prompt type


# Git operations types
CommitDict = Dict[str, str]
DiffType = Literal["staged", "unstaged"]
RemoteOperation = Literal["add", "remove", "set-url"]
TagOperation = Literal["create", "delete", "push"]
StashOperation = Literal["save", "pop", "apply", "drop", "list"]

# AI types
PromptType = Literal["simple", "advanced"]
Message = Dict[str, str]
CommitContext = Dict[str, Any]

# Common type aliases
OptionalConfig = Optional[GitConfig]
