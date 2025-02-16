"""
Functions for building commit messages using AI.
"""

from git_acp.utils import debug_header, debug_preview, debug_json
from git_acp.ai.client import AIClient
from git_acp.ai.commit_prompts import (
    ADVANCED_COMMIT_SYSTEM_PROMPT,
    SIMPLE_COMMIT_SYSTEM_PROMPT,
)
from git_acp.commit.prompt_builder import (
    create_advanced_commit_message_prompt,
    create_simple_commit_message_prompt,
)


def build_advanced_commit_message(context: dict, *, verbose: bool = False) -> str:
    """
    Build an advanced commit message using repository context.

    Args:
        context: Dictionary containing git context.
        verbose: Whether to log debug information.

    Returns:
        A commit message string.
    """
    prompt = create_advanced_commit_message_prompt(context)

    if verbose:
        debug_header("Building Advanced Commit Message")
        debug_json(context, indent=4)
        debug_preview(f"Generated Prompt:\n{prompt}")

    client = AIClient()
    messages = [
        {"role": "system", "content": ADVANCED_COMMIT_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        commit_message = client.chat_completion(messages).strip()

        if verbose:
            debug_preview(f"Generated Commit Message:\n{commit_message}")

        return commit_message
    except (ConnectionError, TimeoutError, ValueError) as e:
        if verbose:
            debug_preview(f"Error Generating Commit Message:\n{str(e)}")
        # Fallback to a basic commit message
        return f"update: {context.get('staged_changes', '').split()[0]}"


def build_simple_commit_message(context: dict, config=None) -> str:
    """
    Build a simple commit message using repository context.

    Args:
        context: Dictionary containing git context.
        config: Optional configuration.

    Returns:
        A commit message string.
    """
    prompt = create_simple_commit_message_prompt(context, config)

    if config and getattr(config, "verbose", False):
        debug_header("Building Simple Commit Message")
        debug_json(context, indent=4)
        debug_preview(f"Generated Prompt:\n{prompt}")

    client = AIClient(config)
    messages = [
        {"role": "system", "content": SIMPLE_COMMIT_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        commit_message = client.chat_completion(messages).strip()

        if config and getattr(config, "verbose", False):
            debug_preview(f"Generated Commit Message:\n{commit_message}")

        return commit_message
    except (ConnectionError, TimeoutError, ValueError) as e:
        if config and getattr(config, "verbose", False):
            debug_preview(f"Error Generating Commit Message:\n{str(e)}")
        # Fallback to a basic commit message
        return f"update: {context.get('staged_changes', '').split()[0]}"
