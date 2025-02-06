"""CLI package for git-acp."""

from .commit import main
from .pr import pr

__all__ = ["main", "pr"]
