"""Overall commit message generation logic using AI."""

import questionary

from git_acp.ai.client import AIClient
from git_acp.utils.types import GitConfig
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
    run_git_command,
)
from git_acp.utils import (
    debug_header,
    debug_item,
    ai_border_message,
    status,
    success,
)


def get_commit_context(config) -> dict:
    """
    Gather git context information for commit message generation.

    Args:
        config: GitConfig object.

    Returns:
        A context dictionary.
    """
    try:
        if config.verbose:
            debug_header("Gathering commit context")
        else:
            status("📝 Analyzing repository changes...")
        staged_changes = get_diff("staged", config)
        if not staged_changes:
            staged_changes = get_diff("unstaged", config)
        recent_commits = get_recent_commits(config=config)
        commit_patterns = analyze_commit_patterns(recent_commits, config)
        # Get file paths from git status
        stdout, _ = run_git_command(["git", "status", "--porcelain"], config)
        file_paths = [line.split()[-1] for line in stdout.split("\n") if line.strip()]
        related_commits = find_related_commits(file_paths, config=config)
        context = {
            "staged_changes": staged_changes,
            "recent_commits": recent_commits,
            "related_commits": related_commits,
            "commit_patterns": commit_patterns,
        }
        success("Successfully gathered commit context")
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
    if not config.ai_config.interactive:
        return message
    ai_border_message(
        message=message,
        title="Generated Commit Message",
        message_style=None,
    )
    if questionary.confirm("Would you like to edit this message?").ask():
        edited = questionary.text("Edit commit message:", default=message).ask()
        if edited and edited.strip():
            return edited.strip()
    return message


def generate_commit_message(config: GitConfig) -> str:
    """
    Generate a commit message using AI.

    Args:
        config: GitConfig object.

    Returns:
        The generated (and possibly edited) commit message.
    """
    try:
        if config.verbose:
            debug_header("Generating commit message with AI")
        else:
            status("🤖 Generating commit message...")
        client = AIClient(config)
        if config.verbose:
            debug_header("Gathering commit context")
        else:
            status("📝 Analyzing repository changes...")
        context = get_commit_context(config)
        if config.ai_config.prompt_type == "advanced":
            prompt = create_advanced_commit_message_prompt(context, config)
        else:
            prompt = create_simple_commit_message_prompt(context, config)
        messages = [{"role": "user", "content": prompt}]
        commit_message = client.chat_completion(messages)
        edited_message = edit_commit_message(commit_message, config)
        success("Successfully generated commit message")
        return edited_message
    except Exception as e:
        if config.verbose:
            debug_header("Error generating commit message")
            debug_item(config, "Error", str(e))
        raise GitError(f"Failed to generate commit message: {str(e)}") from e
