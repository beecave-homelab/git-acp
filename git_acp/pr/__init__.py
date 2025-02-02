"""
PR module for handling Pull Request generation and submission.

This module provides functionality for building and submitting pull requests,
including AI-powered generation of PR descriptions.
"""

from .builder import build_pr_markdown
from .github import create_pull_request

__all__ = ['build_pr_markdown', 'create_pull_request'] 