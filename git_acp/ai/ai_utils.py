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
    ADVANCED_PROMPT_CONTEXT_RATIO,
    COLORS,
    DEFAULT_CONTEXT_WINDOW,
    DEFAULT_NUM_RECENT_COMMITS,
    DEFAULT_NUM_RELATED_COMMITS,
    MIN_CHANGES_CONTEXT,
    QUESTIONARY_STYLE,
    SIMPLE_PROMPT_CONTEXT_RATIO,
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


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a text string.

    Simple estimation: ~4 characters per token for English text.
    This is a rough approximation for context management.

    Args:
        text: The text to estimate tokens for.

    Returns:
        Estimated token count.
    """
    return max(1, len(text) // 4)


def calculate_context_budget(
    context_window: int, prompt_type: str = "simple"
) -> tuple[int, int]:
    """Calculate available token budget for prompt and response.

    Args:
        context_window: Total available context window in tokens.
        prompt_type: Type of prompt ("simple" or "advanced").

    Returns:
        Tuple of (max_prompt_tokens, reserved_response_tokens).
    """
    if prompt_type == "simple":
        ratio = SIMPLE_PROMPT_CONTEXT_RATIO
    else:
        ratio = ADVANCED_PROMPT_CONTEXT_RATIO

    max_prompt_tokens = int(context_window * ratio)
    reserved_response_tokens = context_window - max_prompt_tokens

    return max_prompt_tokens, reserved_response_tokens


def truncate_context_for_window(
    context: dict[str, Any], max_tokens: int, prompt_type: str = "simple"
) -> dict[str, Any]:
    """Truncate context to fit within token budget while preserving priority.

    Args:
        context: The full context dictionary.
        max_tokens: Maximum tokens allowed for the context.
        prompt_type: Type of prompt for priority adjustments.

    Returns:
        Truncated context dictionary.
    """
    # Start with full context
    truncated = context.copy()

    # Calculate current token usage
    current_tokens = estimate_tokens(json.dumps(truncated, indent=2))

    if current_tokens <= max_tokens:
        return truncated

    # Priority order for truncation
    if prompt_type == "simple":
        # Simple: changes > requirements > minimal context
        truncation_order = ["related_commits", "recent_commits", "commit_patterns"]
        min_changes = MIN_CHANGES_CONTEXT
    else:
        # Advanced: related_commits > recent_commits > patterns > changes
        truncation_order = ["related_commits", "recent_commits", "commit_patterns"]
        min_changes = MIN_CHANGES_CONTEXT // 2  # Less restrictive for advanced

    # Truncate by priority
    for key in truncation_order:
        if key in truncated and current_tokens > max_tokens:
            if key == "related_commits":
                # Truncate related commits first
                original = truncated[key]
                truncated[key] = original[: max(0, len(original) // 2)]
            elif key == "recent_commits":
                # Truncate recent commits
                original = truncated[key]
                truncated[key] = original[: max(1, len(original) // 2)]
            elif key == "commit_patterns":
                # Simplify patterns (remove less important data)
                patterns = truncated[key].copy()
                if "types" in patterns and len(patterns["types"]) > 5:
                    # Keep only top 5 types
                    patterns["types"] = dict(list(patterns["types"].items())[:5])
                if "scopes" in patterns and len(patterns["scopes"]) > 3:
                    # Keep only top 3 scopes
                    patterns["scopes"] = dict(list(patterns["scopes"].items())[:3])
                truncated[key] = patterns

            # Recalculate tokens
            current_tokens = estimate_tokens(json.dumps(truncated, indent=2))

    # Final check - if still over budget, truncate staged changes
    if current_tokens > max_tokens and "staged_changes" in truncated:
        changes = truncated["staged_changes"]
        changes_tokens = estimate_tokens(changes)
        allowed_changes_tokens = max_tokens - (current_tokens - changes_tokens)

        if allowed_changes_tokens < min_changes:
            # Ensure minimum changes context
            allowed_changes_tokens = min_changes

        # Truncate changes to fit
        if changes_tokens > allowed_changes_tokens:
            lines = changes.split("\n")
            truncated_lines = []
            current_line_tokens = 0

            for line in lines:
                line_tokens = estimate_tokens(line + "\n")
                if current_line_tokens + line_tokens <= allowed_changes_tokens:
                    truncated_lines.append(line)
                    current_line_tokens += line_tokens
                else:
                    # Add truncated indicator
                    truncated_lines.append(
                        f"... [truncated {len(lines) - len(truncated_lines)} lines]"
                    )
                    break

            truncated["staged_changes"] = "\n".join(truncated_lines)

    return truncated


def create_structured_advanced_commit_message_prompt(
    context: dict[str, Any],
    config: OptionalConfig = None,
) -> str:
    """Create a structured AI prompt for generating a contextually-aware commit message.

    Args:
        context: Git context information.
        config: Optional configuration settings.

    Returns:
        Structured prompt for the AI model.
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

    # Get commit patterns for style guidance
    patterns = context["commit_patterns"]
    scopes = list(patterns.get("scopes", {}).keys())[:3]  # Top 3 scopes
    scope_text = (
        ", ".join(f"`{scope}`" for scope in scopes) if scopes else "not commonly used"
    )

    prompt = f"""<task>
Generate an accurate, contextually-aware conventional commit message
for the provided git changes.
</task>

<repository_context>
- Most common commit type: `{common_type}`
- Recent commit patterns: {json.dumps(recent_messages, indent=2)}
- Related work: {related_json}
- Common scopes: {scope_text}
</repository_context>

<changes>
{context["staged_changes"]}
</changes>

<style_guide>
Follow repository patterns:
- Common type: `{common_type}`
- Typical scope usage: {scope_text}
- Message length: Keep title under 72 characters
</style_guide>

<requirements>
1. Match repository commit style and patterns
2. Be specific about changes and rationale
3. Reference related commits when relevant
4. Use appropriate commit type and scope
5. Keep title under 72 chars, body well-formatted
</requirements>

<output_format>
type(scope): descriptive title

Detailed explanation of what changed and why.
Reference to related work if applicable.
</output_format>"""

    if config and config.verbose:
        debug_header("Generated structured advanced prompt preview:")
        debug_preview(prompt)

    return prompt


def create_structured_simple_commit_message_prompt(
    context: dict[str, Any],
    config: OptionalConfig = None,
) -> str:
    """Create a structured AI prompt for generating a conventional commit message.

    Args:
        context: Git context information.
        config: Optional configuration settings.

    Returns:
        Structured prompt for the AI model.
    """
    prompt = f"""<task>
Generate a conventional commit message for the provided git changes.
</task>

<changes>
{context["staged_changes"]}
</changes>

<requirements>
1. Use conventional commit format: type: description
2. Be specific about what changed
3. Keep under 72 characters for title
4. Add body only if explanation needed
</requirements>

<output_format>
type: brief description

[Optional detailed explanation]
</output_format>"""

    if config and config.verbose:
        debug_header("Generated structured simple prompt preview:")
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
            if config.prompt and config.prompt.strip():
                debug_item("Prompt override", "enabled")

        # Initialize AI client
        ai_client = AIClient(config)

        if config and config.verbose:
            debug_header("Gathering repository context")
        context = get_commit_context(config)

        if config and config.verbose:
            debug_header("Creating AI prompt")

        # Calculate context budget and apply smart truncation
        context_window = config.context_window or DEFAULT_CONTEXT_WINDOW
        max_prompt_tokens, reserved_response_tokens = calculate_context_budget(
            context_window, config.prompt_type
        )

        # Apply context window management
        if config.prompt_type == "simple":
            # Simple mode: more aggressive truncation for local usage
            truncated_context = truncate_context_for_window(
                context, max_prompt_tokens, "simple"
            )
        else:
            # Advanced mode: preserve more context for accuracy
            truncated_context = truncate_context_for_window(
                context, max_prompt_tokens, "advanced"
            )

        # Create prompt based on configuration, allowing an explicit override.
        if config.prompt and config.prompt.strip():
            prompt = config.prompt.strip()
        elif config.prompt_type == "advanced":
            prompt = create_structured_advanced_commit_message_prompt(
                truncated_context, config
            )
        else:
            prompt = create_structured_simple_commit_message_prompt(
                truncated_context, config
            )

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
    "create_structured_advanced_commit_message_prompt",
    "create_structured_simple_commit_message_prompt",
    "get_commit_context",
    "edit_commit_message",
    "generate_commit_message",
    "calculate_context_budget",
    "truncate_context_for_window",
    "estimate_tokens",
]
