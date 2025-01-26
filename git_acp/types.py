"""Type definitions and aliases for git-acp package.

This module defines custom types and type aliases used throughout the package,
including configuration types, git operation types, and AI-related types.
"""

from typing import TypeVar, Dict, List, Optional, Any, Literal

# Configuration type
GitConfig = TypeVar('GitConfig')

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
CommitPatterns = Dict[str, Dict[str, int]]

# Common type aliases
JsonDict = Dict[str, Any]
OptionalConfig = Optional[GitConfig] 