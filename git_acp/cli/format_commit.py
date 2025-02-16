"""CLI-specific formatting helpers."""

from git_acp.git.commit_type import CommitType
from git_acp.config.constants import COMMIT_TYPES
from git_acp.utils.formatting import warning, debug_item
from git_acp.utils.types import GitConfig


def format_commit_message(
    commit_type: CommitType, message: str, config: GitConfig
) -> str:
    """
    Format a commit message using conventional commits style.

    Args:
        commit_type: The commit type (e.g., CommitType enum).
        message: The raw commit message.
        config: The Git configuration object.

    Returns:
        A formatted commit message.
    """
    lines = message.split("\n")
    title = lines[0].strip()
    description = (
        "\n".join(line.strip() for line in lines[1:]) if len(lines) > 1 else ""
    )

    # Get full type string with emoji from constants
    try:
        full_type = COMMIT_TYPES[commit_type.name]
        if " " not in full_type:
            if config.verbose:
                warning(
                    f"Invalid COMMIT_TYPES format for {commit_type.name}: '{full_type}'"
                )
            full_type = commit_type.value
    except KeyError:
        if config.verbose:
            warning(f"Missing COMMIT_TYPES entry for {commit_type.name}")
        full_type = commit_type.value

    type_str, _, emoji_str = full_type.partition(" ")

    if config.verbose:
        debug_item(
            config,
            "Commit Type Parsing",
            f"Raw: '{full_type}' | Type: '{type_str}' | Emoji: '{emoji_str}'",
        )

    formatted = f"{type_str}{' ' + emoji_str if emoji_str else ''}: {title}"

    if description:
        formatted += f"\n\n{description}"

    return formatted
