"""Overall commit message generation logic using AI."""

from git_acp.ai.client import AIClient
from git_acp.commit.prompt_builder import (
    create_advanced_commit_message_prompt,
    create_simple_commit_message_prompt,
)
from git_acp.git import (
    get_diff,
    get_recent_commits,
    find_related_commits,
    analyze_commit_patterns,
    GitError,
)
from git_acp.utils import debug_header, debug_item, debug_preview
from rich import print as rprint
import questionary
from rich.panel import Panel


def get_commit_context(config) -> dict:
    """
    Gather git context information for commit message generation.

    Args:
        config: GitConfig object.

    Returns:
        A context dictionary.
    """
    try:
        debug_header("Gathering commit context")
        staged_changes = get_diff("staged", config)
        if not staged_changes:
            staged_changes = get_diff("unstaged", config)
        recent_commits = get_recent_commits(config=config)
        commit_patterns = analyze_commit_patterns(recent_commits, config)
        related_commits = find_related_commits(staged_changes, config=config)
        context = {
            "staged_changes": staged_changes,
            "recent_commits": recent_commits,
            "related_commits": related_commits,
            "commit_patterns": commit_patterns,
        }
        return context
    except Exception as e:
        raise GitError(f"Failed to gather commit context: {str(e)}") from e


def edit_commit_message(message: str, config) -> str:
    """
    Allow the user to edit the AI-generated commit message.

    Args:
        message: The AI-generated message.
        config: GitConfig object.

    Returns:
        The (possibly edited) commit message.
    """
    if not config.interactive:
        return message
    rprint(Panel(message, title="Generated Commit Message"))
    if questionary.confirm("Would you like to edit this message?").ask():
        edited = questionary.text("Edit commit message:", default=message).ask()
        if edited and edited.strip():
            return edited.strip()
    return message


def generate_commit_message(config) -> str:
    """
    Generate a commit message using AI.

    Args:
        config: GitConfig object.

    Returns:
        The generated (and possibly edited) commit message.
    """
    try:
        debug_header("Generating commit message with AI")
        client = AIClient(config)
        context = get_commit_context(config)
        if config.prompt_type == "advanced":
            prompt = create_advanced_commit_message_prompt(context, config)
        else:
            prompt = create_simple_commit_message_prompt(context, config)
        messages = [{"role": "user", "content": prompt}]
        commit_message = client.chat_completion(messages)
        edited_message = edit_commit_message(commit_message, config)
        return edited_message
    except Exception as e:
        debug_header("Error generating commit message")
        debug_item("Error", str(e))
        raise GitError(f"Failed to generate commit message: {str(e)}") from e
