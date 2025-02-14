#!/usr/bin/env python3

"""Command-line interface for Git Add-Commit-Push automation.

This module provides a command-line interface for automating
Git operations with enhanced features:
- Interactive file selection for staging
- AI-powered commit message generation using Ollama
- Smart commit type classification
- Conventional commits format support
- Rich terminal output with progress indicators
"""

import sys
from typing import List, Optional
from dataclasses import dataclass, field

import click
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich import print as rprint

from git_acp.git import (
    GitError,
    get_current_branch,
    git_add,
    git_commit,
    git_push,
    get_changed_files,
    unstage_files,
    CommitType,
    classify_commit_type,
    setup_signal_handlers,
)
from git_acp.ai import generate_commit_message
from git_acp.config import COLORS, QUESTIONARY_STYLE
from git_acp.utils import GitConfig
from git_acp.utils.types import AIConfig
from git_acp.utils.formatting import (
    success,
    status,
    ai_border_message,
)
from git_acp.cli.pr import pr

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


def select_files(changed_files: List[str]) -> List[str]:
    """Present an interactive selection menu for changed files.

    Args:
        changed_files: List of files that have changes

    Returns:
        List[str]: Selected files for staging

    Raises:
        GitError: If no files are selected
    """
    # Add "All files" option at the top
    choices = [{"name": "All files", "value": changed_files, "checked": False}]

    # Add individual files
    choices.extend([{"name": f, "value": [f], "checked": False} for f in changed_files])

    selected = questionary.checkbox(
        "Select files to stage (space to select, enter to confirm):",
        choices=choices,
        style=questionary.Style(QUESTIONARY_STYLE),
    ).ask()

    if selected is None:  # User cancelled
        raise GitError("Operation cancelled by user")

    # Flatten the list of selected files
    return [item for sublist in selected for item in sublist]


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

    if config.skip_confirmation:
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
        unstage_files()  # Unstage files before raising error
        raise GitError("Operation cancelled by user.")
    elif not selected_types or len(selected_types) != 1:  # No selection made
        unstage_files()  # Unstage files before raising error
        raise GitError("No commit type selected.")

    return selected_types[0]


def handle_file_selection(config: GitConfig) -> List[str]:
    """Handle the file selection process.

    Args:
        config: GitConfig instance containing configuration options

    Returns:
        List[str]: Selected files for staging

    Raises:
        GitError: If no files are selected or available
    """
    if config.files:
        return config.files.split()

    changed_files = get_changed_files()
    if not changed_files:
        rprint(
            Panel(
                "No changes detected in the repository.",
                title="No Changes",
                border_style="yellow",
            )
        )
        sys.exit(0)

    selected_files = select_files(changed_files)
    if not selected_files:
        rprint(
            Panel(
                "No files selected for commit.",
                title="No Selection",
                border_style="yellow",
            )
        )
        sys.exit(0)

    return selected_files


def handle_commit_type(config: GitConfig, specified_type: Optional[str]) -> CommitType:
    """Handle commit type selection.

    Args:
        config: GitConfig instance containing configuration options
        specified_type: Optional manually specified commit type

    Returns:
        CommitType: Selected commit type
    """
    if specified_type:
        return CommitType.from_str(specified_type)

    suggested_type = classify_commit_type(config)
    status("Analyzing changes to suggest commit type")

    if specified_type:
        status(f"Using specified commit type: {suggested_type.value}")
        return suggested_type

    selected_type = select_commit_type(config, suggested_type)
    success("Commit type selected successfully")
    return selected_type


@dataclass
class CommitOptions:
    """Options for the commit command."""

    files: Optional[List[str]] = None
    message: Optional[str] = None
    branch: Optional[str] = None
    commit_type: Optional[str] = None
    ai_options: dict = field(
        default_factory=lambda: {
            "use_ollama": False,
            "interactive": False,
            "prompt_type": "advanced",
        }
    )
    no_confirm: bool = False
    verbose: bool = False


@click.group()
@click.version_option()
def main():
    """Automate git add, commit, and push operations with smart features.

    \b
    Features:
    - Interactive file selection for staging
    - AI-powered commit message generation
    - Smart commit type classification
    - Conventional commits format support
    - Rich terminal output with progress indicators
    - Automated PR creation with AI-powered descriptions

    \b
    Commands:
    - commit: Basic git workflow (add, commit, push)
    - pr: Create pull requests with AI-generated descriptions
    """


@main.command(name="commit")
@click.option(
    "-a",
    "--add",
    "files_to_add",
    multiple=True,
    help=(
        "Specify files to stage for commit. If not provided, shows an interactive file "
        "selection menu."
    ),
)
@click.option(
    "-m",
    "--message",
    help=(
        "Custom commit message. If not provided with --ollama, defaults to 'Automated "
        "commit'."
    ),
    metavar="<message>",
)
@click.option(
    "-b",
    "--branch",
    help=(
        "Target branch for push operation. If not specified, uses the current active "
        "branch."
    ),
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
    help="Use Ollama AI to generate a commit message based on your changes.",
)
@click.option(
    "-i",
    "--interactive",
    is_flag=True,
    help=(
        "Enable interactive mode to review and edit the AI-generated commit message. "
        "Only works with --ollama."
    ),
)
@click.option(
    "-p",
    "--prompt-type",
    type=click.Choice(["simple", "advanced"], case_sensitive=False),
    default="advanced",
    help=(
        "Select AI prompt complexity for commit message generation. 'simple' for basic "
        "messages, 'advanced' for detailed analysis."
    ),
    metavar="<type>",
)

# General Options Group
@click.option(
    "-nc",
    "--no-confirm",
    is_flag=True,
    help="Skip all confirmation prompts and proceed automatically.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output mode to show debugging information during execution.",
)
def commit_cmd(
    files_to_add,
    message,
    branch,
    commit_type,
    ollama,
    interactive,
    prompt_type,
    no_confirm,
    verbose,
):
    """Execute git add, commit, and push operations.

    \b
    This command combines three git operations:
    1. Staging files (git add)
    2. Creating a commit (git commit)
    3. Pushing changes (git push)

    \b
    Features:
    - Interactive file selection
    - AI-powered commit messages
    - Smart commit type detection
    - Conventional commits format
    """
    options = CommitOptions(
        files=list(files_to_add) if files_to_add else None,
        message=message,
        branch=branch,
        commit_type=commit_type,
        ai_options={
            "use_ollama": ollama,
            "interactive": interactive,
            "prompt_type": prompt_type,
        },
        no_confirm=no_confirm,
        verbose=verbose,
    )
    commit(options)


def commit(options: CommitOptions):
    """Internal function to handle the commit logic."""
    setup_signal_handlers()

    try:
        # Create AIConfig first
        ai_config = AIConfig(
            use_ollama=options.ai_options["use_ollama"],
            interactive=options.ai_options["interactive"],
            prompt_type=options.ai_options["prompt_type"].lower(),
            verbose=options.verbose,
        )

        # Then create GitConfig with the AIConfig
        config = GitConfig(
            files=" ".join(options.files) if options.files else "",
            message=options.message or "Automated commit",
            branch=options.branch or get_current_branch(),
            ai_config=ai_config,
            skip_confirmation=options.no_confirm,
            verbose=options.verbose,
        )

        selected_files = handle_file_selection(config)
        git_add(selected_files, config)

        if config.ai_config.use_ollama:
            try:
                config.message = generate_commit_message(config)
            except KeyboardInterrupt:
                unstage_files(config)
                rprint(
                    Panel(
                        "AI generation cancelled by user",
                        title="Cancelled",
                        border_style="yellow",
                    )
                )
                sys.exit(0)
            except GitError as e:
                unstage_files(config)
                if isinstance(e, KeyboardInterrupt):
                    rprint(
                        Panel(
                            "AI generation cancelled by user",
                            title="Cancelled",
                            border_style="yellow",
                        )
                    )
                    sys.exit(0)
                if not Confirm.ask(
                    "Would you like to continue with a manual commit message?"
                ):
                    unstage_files(config)
                    sys.exit(1)

        if not config.message:
            raise GitError(
                "No commit message provided. Please specify a message with -m or use "
                "--ollama."
            )

        selected_type = handle_commit_type(config, options.commit_type)
        formatted_message = format_commit_message(selected_type, config.message)

        if not config.skip_confirmation:
            ai_border_message(
                message=formatted_message,
                title="Commit Message",
                message_style=None,
            )
            if not Confirm.ask("Do you want to proceed?"):
                unstage_files(config)
                sys.exit(0)

        git_commit(formatted_message, config)
        git_push(config.branch, config)

    except KeyboardInterrupt:
        unstage_files(config)
        rprint(
            Panel(
                "Operation cancelled by user", title="Cancelled", border_style="yellow"
            )
        )
        sys.exit(0)
    except GitError as e:
        # Handle git-related errors
        unstage_files(config)
        rprint(
            Panel(
                str(e),
                title="Git Error",
                border_style="red",
                subtitle=e.suggestion if hasattr(e, "suggestion") else None,
            )
        )
        sys.exit(1)
    except (EOFError, KeyError) as e:
        # Handle questionary/prompt toolkit errors
        unstage_files()
        rprint(
            Panel(
                (
                    f"[{COLORS['error']}]User interface error:[/{COLORS['error']}]\n"
                    f"{str(e)}\n\n"
                    "Suggestion: Try running the command again in a different terminal."
                ),
                title="UI Error",
                border_style="red",
            )
        )
        sys.exit(1)
    except (OSError, IOError) as e:
        # Handle system and I/O errors
        unstage_files()
        rprint(
            Panel(
                (
                    f"[{COLORS['error']}]System or I/O error:[/{COLORS['error']}]\n"
                    f"{str(e)}\n\n"
                    "Suggestion: Check file permissions and system resources."
                ),
                title="System Error",
                border_style="red",
            )
        )
        sys.exit(1)
    except ValueError as e:
        # Handle value/parsing errors
        unstage_files()
        rprint(
            Panel(
                (
                    f"[{COLORS['error']}]Invalid value or format:[/{COLORS['error']}]\n"
                    f"{str(e)}\n\n"
                    "Suggestion: Check your input values and configuration."
                ),
                title="Value Error",
                border_style="red",
            )
        )
        sys.exit(1)


# Add the PR command to the CLI group
main.add_command(pr)

if __name__ == "__main__":
    main()
