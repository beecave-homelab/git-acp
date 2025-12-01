"""AI-powered commit message generation utilities.

This module provides functions for generating commit messages using AI models
with support for both simple and advanced context-aware generation.
"""

import json
from typing import Any

import questionary
from rich import print as rprint
from rich.panel import Panel

from git_acp.ai.client import AIClient
from git_acp.config import (
    COLORS,
    DEFAULT_NUM_RECENT_COMMITS,
    DEFAULT_NUM_RELATED_COMMITS,
    QUESTIONARY_STYLE,
)
from git_acp.git import (
    GitError,
    analyze_commit_patterns,
    find_related_commits,
    get_diff,
    get_recent_commits,
)
from git_acp.utils import (
    GitConfig,
    OptionalConfig,
    debug_header,
    debug_item,
    debug_preview,
)


def create_advanced_commit_message_prompt(
    context: dict[str, Any],
    config: OptionalConfig = None,
) -> str:
    """Create an AI prompt for generating a commit message.

    Args:
        context (Dict[str, Any]): Git context information.
        config (OptionalConfig | None): Optional configuration settings.

    Returns:
        str: Generated prompt for the AI model.
    """
    # Get most common commit type from recent commits
    commit_types = context["commit_patterns"]["types"]
    common_type = (
        max(commit_types.items(), key=lambda x: x[1])[0] if commit_types else "feat"
    )

    # Format recent commit messages for context
    recent_messages = [c["message"] for c in context["recent_commits"]]
    related_messages = [c["message"] for c in context["related_commits"]]
    related_json = json.dumps(related_messages, indent=2) if related_messages else "[]"

    prompt = (
        "Generate a concise and descriptive commit message for the following "
        "changes:\n\n"
        "Changes to commit:\n"
        f"{context['staged_changes']}\n\n"
        "Repository context:\n"
        f"- Most used commit type: {common_type}\n"
        "- Recent commits:\n"
        f"{json.dumps(recent_messages, indent=2)}\n\n"
        "Related commits:\n"
        f"{related_json}"
        "\n\n"
        "Requirements:\n"
        "1. Follow the repository's commit style (type: description)\n"
        "2. Be specific about what changed and why\n"
        "3. Reference related work if relevant\n"
        "4. Keep it concise but descriptive"
    )
    if config and config.verbose:
        debug_header("Generated prompt preview:")
        debug_preview(prompt)

    return prompt


def get_commit_context(config: GitConfig) -> dict[str, Any]:
    """Gather git context information for commit message generation.

    Args:
        config (GitConfig): Configuration options.

    Returns:
        Dict[str, Any]: Staged changes, commit history, and patterns.

    Raises:
        GitError: If unable to gather context information.
    """
    try:
        if config and config.verbose:
            debug_header("Starting context gathering")

        # Get staged changes
        staged_changes = get_diff("staged", config)
        if not staged_changes:
            if config and config.verbose:
                debug_header("No staged changes, checking working directory")
            staged_changes = get_diff("unstaged", config)

        if config and config.verbose:
            debug_header("Fetching commit history")
        recent_commits = get_recent_commits(DEFAULT_NUM_RECENT_COMMITS, config)

        if config and config.verbose:
            debug_header("Validating commit data")

        # Analyze commit patterns
        commit_patterns = analyze_commit_patterns(recent_commits, config)

        if config and config.verbose:
            debug_header("Commit statistics:")
            debug_item("Recent commits", str(len(recent_commits)))
            debug_item(
                "Common types",
                ", ".join(commit_patterns["types"].keys()),
            )
            debug_item(
                "Common scopes",
                ", ".join(commit_patterns["scopes"].keys()),
            )

        if config and config.verbose:
            debug_header("Analyzing commit patterns")

        # Find related commits based on staged changes
        related_commits = find_related_commits(
            staged_changes, DEFAULT_NUM_RELATED_COMMITS, config
        )

        context = {
            "staged_changes": staged_changes,
            "recent_commits": recent_commits,
            "related_commits": related_commits,
            "commit_patterns": commit_patterns,
        }

        if config and config.verbose:
            debug_header("Context preparation complete")
            debug_item(
                "Context size",
                str(len(json.dumps(context))),
            )

        return context

    except GitError as e:
        raise GitError(f"Failed to gather commit context: {str(e)}") from e


def create_simple_commit_message_prompt(
    context: dict[str, Any],
    config: OptionalConfig = None,
) -> str:
    """Create a simple AI prompt for generating a commit message.

    Args:
        context (Dict[str, Any]): Git context information.
        config (OptionalConfig | None): Optional configuration settings.

    Returns:
        str: Generated prompt for the AI model.
    """
    prompt = (
        "Generate a concise and descriptive commit message for the following "
        "changes:\n\n"
        f"{context['staged_changes']}\n\n"
        "Requirements:\n"
        "1. Follow conventional commit format (type: description)\n"
        "2. Be specific about what changed\n"
        "3. Keep it concise but descriptive"
    )
    if config and config.verbose:
        debug_header("Generated simple prompt preview:")
        debug_preview(prompt)

    return prompt


def edit_commit_message(message: str, config: GitConfig) -> str:
    """Allow user to edit the AI-generated commit message.

    Args:
        message: The AI-generated commit message
        config: GitConfig instance containing configuration options

    Returns:
        str: The edited commit message
    """
    if not config.interactive:
        return message

    if config and config.verbose:
        debug_header("Editing commit message")

    # Show the message in a panel for review
    rprint(
        Panel(
            message,
            title="Generated Commit Message",
            border_style=COLORS["ai_message_border"],
        )
    )

    # Ask if user wants to edit
    if questionary.confirm(
        "Would you like to edit this message?",
        style=questionary.Style(QUESTIONARY_STYLE),
    ).ask():
        # Let user edit the message
        edited = questionary.text(
            "Edit commit message:",
            default=message,
            style=questionary.Style(QUESTIONARY_STYLE),
        ).ask()

        if edited and edited.strip():
            if config and config.verbose:
                debug_header("Message edited")
                debug_preview(edited)
            return edited.strip()

    return message


def generate_commit_message(config: GitConfig) -> str:
    """Generate a commit message using AI.

    Args:
        config: GitConfig instance containing configuration options

    Returns:
        str: The generated commit message

    Raises:
        GitError: If message generation fails
    """
    try:
        if config and config.verbose:
            debug_header("Generating commit message with AI")
            debug_item("Prompt type", config.prompt_type)

        # Initialize AI client
        ai_client = AIClient(config)

        if config and config.verbose:
            debug_header("Gathering repository context")
        context = get_commit_context(config)

        if config and config.verbose:
            debug_header("Creating AI prompt")

        # Create prompt based on configuration
        if config.prompt_type == "advanced":
            prompt = create_advanced_commit_message_prompt(context, config)
        else:
            prompt = create_simple_commit_message_prompt(context, config)

        # Send request to AI model
        messages = [{"role": "user", "content": prompt}]
        commit_message = ai_client.chat_completion(messages)

        if config and config.verbose:
            debug_header("Generated commit message")
            debug_preview(commit_message)

        # Allow user to edit the message
        edited_message = edit_commit_message(commit_message, config)

        if config and config.verbose:
            debug_header("Edited commit message")
            debug_preview(edited_message)

        return edited_message

    except GitError as e:
        if config and config.verbose:
            debug_header("Error generating commit message")
            debug_item("Error", str(e))
        raise GitError(f"Failed to generate commit message: {str(e)}") from e


__all__ = [
    "AIClient",
    "create_advanced_commit_message_prompt",
    "create_simple_commit_message_prompt",
    "get_commit_context",
    "edit_commit_message",
    "generate_commit_message",
]
