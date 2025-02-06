"""
Functions for building commit message prompts.
"""

import json
from git_acp.utils import debug_header, debug_preview
from git_acp.ai.commit_prompts import (
    ADVANCED_COMMIT_SYSTEM_PROMPT,
    SIMPLE_COMMIT_SYSTEM_PROMPT,
)


def create_advanced_commit_message_prompt(context: dict, config=None) -> str:
    """
    Create an advanced AI prompt using repository context.

    Args:
        context: Dictionary containing git context.
        config: Optional configuration.

    Returns:
        A prompt string.
    """
    commit_types = context["commit_patterns"]["types"]
    common_type = (
        max(commit_types.items(), key=lambda x: x[1])[0] if commit_types else "feat"
    )
    recent_messages = [c["message"] for c in context["recent_commits"]]
    related_messages = [c["message"] for c in context["related_commits"]]

    # Extract requirements from system prompt
    requirements = ADVANCED_COMMIT_SYSTEM_PROMPT.strip().split("\n")[2:]
    requirements_text = "\n".join(requirements)

    prompt = f"""
Generate a concise and descriptive commit message for the following changes:

Changes to commit:
{context['staged_changes']}

Repository context:
- Most used commit type: {common_type}
- Recent commits:
{json.dumps(recent_messages, indent=2)}

Related commits:
{json.dumps(related_messages, indent=2) if related_messages else '[]'}

Requirements:
{requirements_text}
"""
    if config and getattr(config, "verbose", False):
        debug_header("Generated prompt preview:")
        debug_preview(prompt)
    return prompt


def create_simple_commit_message_prompt(context: dict, config=None) -> str:
    """
    Create a simple AI prompt using repository context.

    Args:
        context: Dictionary containing git context.
        config: Optional configuration.

    Returns:
        A prompt string.
    """
    # Extract requirements from system prompt
    requirements = SIMPLE_COMMIT_SYSTEM_PROMPT.strip().split("\n")[2:]
    requirements_text = "\n".join(requirements)

    prompt = f"""
Generate a concise and descriptive commit message for the following changes:

{context['staged_changes']}

Requirements:
{requirements_text}
"""
    if config and getattr(config, "verbose", False):
        debug_header("Generated simple prompt preview:")
        debug_preview(prompt)
    return prompt
