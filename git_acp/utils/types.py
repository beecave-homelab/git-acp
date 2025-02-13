"""Type definitions and aliases for git-acp package.

This module defines custom types and type aliases used throughout the package,
including configuration types, git operation types, and AI-related types.
"""

from typing import Dict, Optional, Any, Literal
from dataclasses import dataclass, field


# Configuration type
@dataclass
class AIConfig:
    """Configuration settings for AI operations.

    Attributes:
        use_ollama: Whether to use Ollama AI for content generation
        model: AI model to use for generation
        prompt_type: Type of prompt to use ('simple' or 'advanced')
        context_type: Type of context to include ('commits', 'diffs', or 'both')
        temperature: Creativity level for AI responses (0.0-1.0)
        timeout: Timeout in seconds for AI requests
        verbose: Whether to show debug information
        interactive: Whether to enable interactive mode for editing messages
    """

    interactive: bool = False
    verbose: bool = False
    use_ollama: bool = False
    prompt_type: str = "simple"
    model: Optional[str] = None
    temperature: float = 0.7
    timeout: float = 120.0
    context_type: str = "both"


@dataclass
class GitConfig:
    """Configuration settings for git operations.

    Attributes:
        files: Files to be added to git staging. Defaults to "." for all files.
        message: Commit message to use. Defaults to "Automated commit".
        branch: Target branch for push operation. If None, uses current branch.
        ai_config: AI configuration settings.
        skip_confirmation: Whether to skip confirmation prompts.
        verbose: Whether to show debug information.
    """

    files: str = "."
    message: str = "Automated commit"
    branch: Optional[str] = None
    ai_config: AIConfig = field(default_factory=AIConfig)
    skip_confirmation: bool = False
    verbose: bool = False


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
