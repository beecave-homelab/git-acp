"""CLI prompts for interactive selection."""

from typing import List

import questionary

from git_acp.config import TERMINAL_SETTINGS
from git_acp.git import GitError
from git_acp.utils.types import GitConfig
from git_acp.utils.formatting import debug_print
from git_acp.git.commit_type import CommitType


def select_files(changed_files: set, config: GitConfig) -> List[str]:
    """
    Present an interactive selection for files.

    Args:
        changed_files: Set of changed files.
        config: GitConfig instance containing configuration options.

    Returns:
        A list of selected files.
    """
    if not changed_files:
        raise GitError("No changed files found to commit.")

    # Single file case
    if len(changed_files) == 1:
        selected_file = next(iter(changed_files))
        debug_print(config, f"Adding file: {selected_file}")
        return [selected_file]

    # Multiple files case
    choices = [{"name": file, "value": file} for file in sorted(changed_files)]
    choices.append({"name": "All files", "value": "."})

    selected = questionary.checkbox(
        "Select files to commit (space to select, enter to confirm):",
        choices=choices,
        style=questionary.Style(TERMINAL_SETTINGS["questionary_style"]),
    ).ask()

    if selected is None or not selected:
        raise GitError("No files selected or operation cancelled.")

    # Handle "All files" selection
    if "." in selected:
        debug_print(config, "Adding all files.")
        return ["."]

    # Return list of selected files
    return [f for f in selected if f]  # Filter out any empty strings


def select_commit_type(config: GitConfig, suggested_type: CommitType) -> CommitType:
    """
    Present an interactive selection for commit type.

    Args:
        config: GitConfig instance containing configuration options
        suggested_type: The suggested commit type based on changes

    Returns:
        CommitType: The selected commit type

    Raises:
        GitError: If no commit type is selected
    """
    # Only auto-select when using --no-confirm flag
    if config.skip_confirmation:
        debug_print(config, f"Auto-selecting commit type: {suggested_type.value}")
        return suggested_type

    # Create choices with suggested type highlighted
    commit_type_choices = []
    for commit_type in CommitType:
        name = (
            f"{commit_type.value} (suggested)"
            if commit_type == suggested_type
            else commit_type.value
        )
        commit_type_choices.append(
            {"name": name, "value": commit_type, "checked": False}
        )

    # Present interactive selection
    selected_types = questionary.checkbox(
        "Select commit type (space to select, enter to confirm):",
        choices=commit_type_choices,
        style=questionary.Style(TERMINAL_SETTINGS["questionary_style"]),
        instruction="(suggested type marked)",
        validate=lambda s: len(s) == 1 or "Please select exactly one commit type",
    ).ask()

    if not selected_types or len(selected_types) != 1:
        raise GitError("No commit type selected")

    return selected_types[0]
