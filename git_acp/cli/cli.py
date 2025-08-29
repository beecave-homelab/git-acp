#!/usr/bin/env python3

"""Command-line interface for Git Add-Commit-Push automation.

This module provides a command-line interface for automating Git operations with enhanced features:
- Interactive file selection for staging
- AI-powered commit message generation using Ollama
- Smart commit type classification
- Conventional commits format support
- Rich terminal output with progress indicators
"""

import glob
import shlex
import sys
from typing import List, Optional, Set

import click
import questionary
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from git_acp.ai import generate_commit_message
from git_acp.config import COLORS, QUESTIONARY_STYLE
import git_acp.git as git_module
from git_acp.git import (
    CommitType,
    GitError,
    classify_commit_type,
    get_current_branch,
    git_add,
    git_commit,
    git_push,
    setup_signal_handlers,
    unstage_files,
)
from git_acp.utils import GitConfig

console = Console()


def debug_print(config: GitConfig, message: str) -> None:
    """Print a debug message if verbose mode is enabled.

    Args:
        config: GitConfig instance containing configuration options
        message: Debug message to print
    """
    if config.verbose:
        rprint(f"[{COLORS['warning']}]Debug: {message}[/{COLORS['warning']}]")


def format_commit_message(commit_type: CommitType, message: str) -> str:
    """Format a commit message according to conventional commits specification.

    Args:
        commit_type: The type of commit
        message: The commit message

    Returns:
        str: The formatted commit message
    """
    lines = message.split("\n")
    title = lines[0]
    description = "\n".join(lines[1:])
    return f"{commit_type.value}: {title}\n\n{description}".strip()


def select_files(changed_files: Set[str]) -> str:
    """Present an interactive selection menu for changed files.

    Args:
        changed_files: Set of files with uncommitted changes

    Returns:
        str: Space-separated list of selected files, with proper quoting
    """
    if not changed_files:
        raise GitError("No changed files found to commit.")

    if len(changed_files) == 1:
        selected_file = next(iter(changed_files))
        rprint(
            f"[{COLORS['warning']}]Adding file:[/{COLORS['warning']}] {selected_file}"
        )
        return f'"{selected_file}"' if " " in selected_file else selected_file

    # Create choices with the original filenames
    choices = []
    for file in sorted(list(changed_files)):
        choices.append(
            {
                "name": file,  # Display name
                "value": file,  # Actual value
            }
        )

    # Add "All files" as the last option
    choices.append({"name": "All files", "value": "All files"})

    # Use a wider display for the checkbox prompt
    selected = questionary.checkbox(
        "Select files to commit (space to select, enter to confirm):",
        choices=choices,
        style=questionary.Style(QUESTIONARY_STYLE),
    ).ask()

    if selected is None:  # User cancelled
        raise GitError("Operation cancelled by user.")
    elif not selected:  # No selection made
        raise GitError("No files selected.")

    if "All files" in selected:
        rprint(f"[{COLORS['warning']}]Adding all files[/{COLORS['warning']}]")
        return "."

    # Print selected files for user feedback
    rprint(f"[{COLORS['warning']}]Adding files:[/{COLORS['warning']}]")
    for file in selected:
        rprint(f"  - {file}")

    # Return files as a space-separated string, properly quoted if needed
    return " ".join(f'"{f}"' if " " in f else f for f in selected)


def select_commit_type(config: GitConfig, suggested_type: CommitType) -> CommitType:
    """
    Present an interactive selection menu for commit types.
    If no_confirm is True, automatically selects the suggested type.

    Args:
        config: GitConfig instance containing configuration options
        suggested_type: The suggested commit type based on changes

    Returns:
        CommitType: The selected commit type

    Raises:
        GitError: If no commit type is selected
    """
    if config.skip_confirmation or suggested_type.value in [
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "test",
        "chore",
        "revert",
    ]:
        if config.verbose:
            debug_print(config, f"Auto-selecting commit type: {suggested_type.value}")
        return suggested_type

    # Create choices list with suggested type highlighted
    commit_type_choices = []
    for commit_type in CommitType:
        # Add (suggested) tag for the suggested type
        name = (
            f"{commit_type.value} (suggested)"
            if commit_type == suggested_type
            else commit_type.value
        )
        choice = {
            "name": name,
            "value": commit_type,
            "checked": False,  # Don't pre-select any option
        }
        if commit_type == suggested_type:
            commit_type_choices.insert(0, choice)  # Put suggested type at the top
        else:
            commit_type_choices.append(choice)

    if config.verbose:
        debug_print(config, f"Suggested commit type: {suggested_type.value}")

    def validate_single_selection(selected_types: List[CommitType]) -> str | bool:
        """
        Validate that exactly one commit type is selected.

        Args:
            selected_types: List of selected commit types

        Returns:
            str | bool: True if valid, error message string if invalid
        """
        if len(selected_types) != 1:
            return "Please select exactly one commit type"
        return True

    selected_types = questionary.checkbox(
        "Select commit type (space to select, enter to confirm):",
        choices=commit_type_choices,
        style=questionary.Style(QUESTIONARY_STYLE),
        instruction=" (suggested type marked)",
        validate=validate_single_selection,
    ).ask()

    if selected_types is None:  # User cancelled
        raise GitError("Operation cancelled by user.")
    elif not selected_types or len(selected_types) != 1:  # No selection made
        raise GitError("No commit type selected.")

    return selected_types[0]


@click.command()
# Git Operations Group
@click.option(
    "-a",
    "--add",
    help='Specify space-separated files/patterns to stage (e.g., "file1.py *.py folder/"). Patterns are globbed recursively (e.g. `**/*.py`). If not provided, interactive selection is used.',
    metavar="<files_or_patterns>",
)
@click.option(
    "-m",
    "--message",
    help="Custom commit message. If not provided with --ollama, defaults to 'Automated commit'.",
    metavar="<message>",
)
@click.option(
    "-b",
    "--branch",
    help="Target branch for push operation. If not specified, uses the current active branch.",
    metavar="<branch>",
)
@click.option(
    "-t",
    "--type",
    "commit_type",
    type=click.Choice(
        ["feat", "fix", "docs", "style", "refactor", "test", "chore", "revert"],
        case_sensitive=False,
    ),
    help="Manually specify the commit type instead of using automatic detection.",
    metavar="<type>",
)
# AI Features Group
@click.option(
    "-o",
    "--ollama",
    is_flag=True,
    help="Use Ollama AI to generate a descriptive commit message based on your changes.",
)
@click.option(
    "-i",
    "--interactive",
    is_flag=True,
    help="Enable interactive mode to review and edit the AI-generated commit message. Only works with --ollama.",
)
@click.option(
    "-p",
    "--prompt-type",
    type=click.Choice(["simple", "advanced"], case_sensitive=False),
    default="advanced",
    help="Select AI prompt complexity for commit message generation. 'simple' for basic messages, 'advanced' for detailed analysis.",
    metavar="<type>",
)
# General Options Group
@click.option(
    "-nc",
    "--no-confirm",
    is_flag=True,
    help="Skip all confirmation prompts and proceed automatically with suggested values.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output mode to show detailed debug information during execution.",
)
def main(
    add: Optional[str],
    message: Optional[str],
    branch: Optional[str],
    ollama: bool,
    interactive: bool,
    no_confirm: bool,
    commit_type: Optional[str],
    verbose: bool,
    prompt_type: str,
) -> None:
    """Automate git add, commit, and push operations with smart features.

    This tool streamlines your git workflow by combining add, commit, and push operations
    with intelligent features like AI-powered commit messages and conventional commits support.

    \b
    Features:
    - Interactive file selection for staging
    - AI-powered commit message generation
    - Smart commit type classification
    - Conventional commits format support
    - Rich terminal output with progress indicators

    \b
    Options are grouped into:
    - Git Operations: Commands for basic git workflow (-a, -m, -b, -t)
    - AI Features: AI-powered commit message generation (-o, -i, -p)
    - General: Program behavior control (-nc, -v)

    """
    # Set up signal handler for graceful interruption
    setup_signal_handlers()

    try:
        processed_add_argument: Optional[str] = None
        if add is not None:
            if not add.strip():
                rprint(
                    f"[{COLORS['warning']}]The -a flag was used with an empty string. No files will be staged based on this argument.[/{COLORS['warning']}]"
                )
                processed_add_argument = ""
            else:
                items_to_process = shlex.split(add)
                resolved_paths: List[str] = []
                unmatched_items: List[str] = []
                for item in items_to_process:
                    expanded_paths = glob.glob(item, recursive=True)
                    if not expanded_paths:
                        unmatched_items.append(item)
                    else:
                        resolved_paths.extend(expanded_paths)

                if unmatched_items:
                    rprint(
                        f"[{COLORS['warning']}]Warning: The following patterns/files provided via -a did not match any filesystem paths: {', '.join(unmatched_items)}[/{COLORS['warning']}]"
                    )

                if not resolved_paths:
                    rprint(
                        f"[{COLORS['info']}]No files or directories matched the criteria from the -a argument. No files will be staged.[/{COLORS['info']}]"
                    )
                    processed_add_argument = ""
                else:
                    unique_paths = list(
                        dict.fromkeys(resolved_paths)
                    )  # Remove duplicates while preserving order
                    processed_add_argument = " ".join(
                        f'"{p}"' if " " in p else p for p in unique_paths
                    )

        config = GitConfig(
            files=processed_add_argument if processed_add_argument is not None else ".",
            message=message or "Automated commit",
            branch=branch,
            use_ollama=ollama,
            interactive=interactive,
            skip_confirmation=no_confirm,
            verbose=verbose,
            prompt_type=prompt_type.lower(),
        )

        if add is None:  # Only run interactive selection if -a was not provided
            try:
                changed_files = git_module.get_changed_files(config)  # config is used for verbose
                if not changed_files:
                    if config.skip_confirmation:
                        rprint(
                            Panel(
                                "No changes detected in the repository. Nothing to do.",
                                title="No Changes",
                                border_style="yellow",
                            )
                        )
                        sys.exit(0)
                    # If not skipping confirmation, select_files will handle empty changed_files by raising an error or specific behavior

                # This line updates config.files with the interactive selection
                config.files = select_files(changed_files)
            except GitError as e:
                if "cancelled by user" in str(e).lower():
                    unstage_files()
                    rprint(
                        Panel(
                            "Operation cancelled by user.",
                            title="Cancelled",
                            border_style="yellow",
                        )
                    )
                else:
                    rprint(
                        Panel(
                            f"[{COLORS['error']}]Error during file selection:[/{COLORS['error']}]\n{str(e)}",
                            title="File Selection Failed",
                            border_style="red",
                        )
                    )
                sys.exit(1)
        elif processed_add_argument == "":  # -a was used but resulted in no files
            rprint(
                Panel(
                    "The -a argument resulted in no files to stage. Nothing to commit.",
                    title="No Files to Stage via -a",
                    border_style="yellow",
                )
            )
            sys.exit(0)

        if not config.branch:
            try:
                config.branch = get_current_branch()
            except GitError as e:
                rprint(
                    Panel(
                        f"[{COLORS['error']}]Error getting current branch:[/{COLORS['error']}]\n{str(e)}\n\n"
                        "Suggestion: Ensure you're in a git repository and have a valid branch.",
                        title="Branch Detection Failed",
                        border_style="red",
                    )
                )
                sys.exit(1)

        # Add files first
        try:
            git_add(config.files, config)  # Pass config for verbose/debug
            # Check if files were staged when -a is used
            if add is not None:  # -a was used
                staged_files = git_module.get_changed_files(config, staged_only=True)
                if not staged_files:
                    # This message is now more specific if -a was used and resolved to something, but nothing was actually changed/staged
                    rprint(
                        Panel(
                            f"No actual changes were found in the files/patterns specified by -a (resolved to: '{config.files}'). Nothing was staged.",
                            title="No Changes Staged via -a",
                            border_style="yellow",
                        )
                    )
                    sys.exit(0)
        except GitError as e:
            rprint(
                Panel(
                    f"[{COLORS['error']}]Error adding files:[/{COLORS['error']}]\n{str(e)}\n\n"
                    "Suggestion: Check file paths and repository permissions.",
                    title="Git Add Failed",
                    border_style="red",
                )
            )
            sys.exit(1)

        try:
            if config.use_ollama:
                try:
                    config.message = generate_commit_message(config)
                except GitError as e:
                    rprint(
                        Panel(
                            f"[{COLORS['error']}]AI commit message generation failed:[/{COLORS['error']}]\n{str(e)}\n\n"
                            "Suggestion: Check Ollama server status and configuration.",
                            title="AI Generation Failed",
                            border_style="red",
                        )
                    )
                    if not Confirm.ask(
                        "Would you like to continue with a manual commit message?"
                    ):
                        unstage_files()
                        sys.exit(1)

            if not config.message:
                raise GitError(
                    "No commit message provided. Please specify a message with -m or use --ollama."
                )

            # Get suggested commit type
            try:
                suggested_type = (
                    CommitType.from_str(commit_type)
                    if commit_type
                    else classify_commit_type(config)
                )
            except GitError as e:
                rprint(
                    Panel(
                        f"[{COLORS['warning']}]Commit type detection failed, defaulting to 'chore':[/{COLORS['warning']}]\n{str(e)}",
                        title="Commit Type Warning",
                        border_style="yellow",
                    )
                )
                suggested_type = CommitType.CHORE

            # Let user select commit type, unless it was specified with -t flag
            rprint(
                f"[{COLORS['bold']}]🤖 Analyzing changes to suggest commit type...[/{COLORS['bold']}]"
            )
            if commit_type:
                selected_type = suggested_type
                rprint(
                    f"[{COLORS['success']}]✓ Using specified commit type: {selected_type.value}[/{COLORS['success']}]"
                )
            else:
                try:
                    selected_type = select_commit_type(config, suggested_type)
                    rprint(
                        f"[{COLORS['success']}]✓ Commit type selected successfully[/{COLORS['success']}]"
                    )
                except GitError as e:
                    if "cancelled by user" in str(e).lower():
                        rprint(
                            Panel(
                                "Operation cancelled by user.",
                                title="Cancelled",
                                border_style="yellow",
                            )
                        )
                    else:
                        rprint(
                            Panel(
                                f"[{COLORS['error']}]Error selecting commit type:[/{COLORS['error']}]\n{str(e)}\n\n"
                                "Suggestion: Try again or specify a commit type with -t.",
                                title="Commit Type Selection Failed",
                                border_style="red",
                            )
                        )
                    unstage_files()
                    sys.exit(1)

            formatted_message = format_commit_message(selected_type, config.message)

            if not config.skip_confirmation:
                rprint(
                    Panel.fit(
                        formatted_message,
                        title=f"[{COLORS['ai_message_header']}]Commit Message[/{COLORS['ai_message_header']}]",
                        border_style=COLORS["ai_message_border"],
                    )
                )
                if not Confirm.ask("Do you want to proceed?"):
                    unstage_files()
                    rprint(
                        Panel(
                            "Operation cancelled by user.",
                            title="Cancelled",
                            border_style="yellow",
                        )
                    )
                    sys.exit(0)
            else:
                rprint(
                    Panel.fit(
                        formatted_message,
                        title=f"[{COLORS['ai_message_header']}]Auto-committing with message[/{COLORS['ai_message_header']}]",
                        border_style=COLORS["ai_message_border"],
                    )
                )

            try:
                git_commit(formatted_message)
            except GitError as e:
                rprint(
                    Panel(
                        f"[{COLORS['error']}]Error committing changes:[/{COLORS['error']}]\n{str(e)}\n\n"
                        "Suggestion: Check if there are changes to commit and try again.",
                        title="Commit Failed",
                        border_style="red",
                    )
                )
                sys.exit(1)

            try:
                git_push(config.branch)
            except GitError as e:
                rprint(
                    Panel(
                        f"[{COLORS['error']}]Error pushing changes:[/{COLORS['error']}]\n{str(e)}\n\n"
                        "Suggestion: Pull latest changes, resolve conflicts if any, and try again.",
                        title="Push Failed",
                        border_style="red",
                    )
                )
                sys.exit(1)

        except Exception as e:
            unstage_files()
            rprint(
                Panel(
                    f"[{COLORS['error']}]An unexpected error occurred:[/{COLORS['error']}]\n{str(e)}\n\n"
                    "Suggestion: Please report this issue if it persists.",
                    title="Unexpected Error",
                    border_style="red bold",
                )
            )
            sys.exit(1)

    except Exception as e:
        rprint(
            Panel(
                f"[{COLORS['error']}]Critical error:[/{COLORS['error']}]\n{str(e)}\n\n"
                "Suggestion: Please check your git repository and configuration.",
                title="Critical Error",
                border_style="red bold",
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
