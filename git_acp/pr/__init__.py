"""
PR module for handling Pull Request generation and submission.

This module provides functionality for building and submitting pull requests,
including AI-powered generation of PR descriptions.
"""

from .builder import (
    build_pr_markdown,
    _build_partial_markdown,
    generate_pr_title,
    generate_pr_summary,
    generate_code_changes,
    generate_reason_for_changes,
    generate_test_plan,
    generate_additional_notes,
    generate_pr_simple,
    review_final_pr,
)
from .github import create_pull_request

__all__ = [
    "build_pr_markdown",
    "_build_partial_markdown",
    "generate_pr_title",
    "generate_pr_summary",
    "generate_code_changes",
    "generate_reason_for_changes",
    "generate_test_plan",
    "generate_additional_notes",
    "generate_pr_simple",
    "review_final_pr",
    "create_pull_request",
]
