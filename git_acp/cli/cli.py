#!/usr/bin/env python3

"""Command-line interface for Git Add-Commit-Push automation.

This module provides a CLI for automating Git operations with enhanced features:

- Interactive file selection for staging
- AI-powered commit message generation using Ollama
- Smart commit type classification
- Conventional commits format support
- Rich terminal output with progress indicators
"""

import glob
import shlex
import sys

import click
from rich import print as rprint
from rich.panel import Panel

from git_acp.cli.interaction import RichQuestionaryInteraction
from git_acp.cli.workflow import GitWorkflow
from git_acp.config import COLORS
from git_acp.git import CommitType, setup_signal_handlers
from git_acp.utils import GitConfig


def format_commit_message(commit_type: CommitType, message: str) -> str:
    """Format a commit message according to conventional commits specification.

    Args:
        commit_type: The type of commit.
        message: The commit message.

    Returns:
        The formatted commit message.
    """
    lines = message.split("\n")
    title = lines[0]
    description = "\n".join(lines[1:])
    return f"{commit_type.value}: {title}\n\n{description}".strip()


def _process_add_argument(add: str | None) -> tuple[str | None, bool]:
    """Process the -a/--add argument, expanding globs.

    Args:
        add: The raw -a argument value.

    Returns:
        Tuple of (processed_files, should_exit_early).
        processed_files is None if -a was not provided.
    """
    if add is None:
        return None, False

    if not add.strip():
        warn = COLORS["warning"]
        rprint(
            f"[{warn}]The -a flag was used with an empty string. "
            f"No files will be staged based on this argument.[/{warn}]"
        )
        return "", False

    items_to_process = shlex.split(add)
    resolved_paths: list[str] = []
    unmatched_items: list[str] = []

    for item in items_to_process:
        expanded_paths = glob.glob(item, recursive=True)
        if not expanded_paths:
            unmatched_items.append(item)
        else:
            resolved_paths.extend(expanded_paths)

    if unmatched_items:
        warn = COLORS["warning"]
        unmatched = ", ".join(unmatched_items)
        rprint(
            f"[{warn}]Warning: The following patterns/files "
            f"provided via -a did not match any filesystem "
            f"paths: {unmatched}[/{warn}]"
        )

    if not resolved_paths:
        info = COLORS["info"]
        rprint(
            f"[{info}]No files or directories matched the "
            f"criteria from the -a argument. "
            f"No files will be staged.[/{info}]"
        )
        return "", False

    # Remove duplicates while preserving order
    unique_paths = list(dict.fromkeys(resolved_paths))
    return " ".join(f'"{p}"' if " " in p else p for p in unique_paths), False


@click.command()
# Git Operations Group
@click.option(
    "-a",
    "--add",
    help=(
        "Specify space-separated files/patterns to stage "
        '(e.g., "file1.py *.py folder/"). Patterns are globbed recursively. '
        "If not provided, interactive selection is used."
    ),
    metavar="<files_or_patterns>",
)
@click.option(
    "-m",
    "--message",
    help=(
        "Custom commit message. If not provided with --ollama, "
        "defaults to 'Automated commit'."
    ),
    metavar="<message>",
)
@click.option(
    "-b",
    "--branch",
    help=(
        "Target branch for push operation. "
        "If not specified, uses the current active branch."
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
    help=(
        "Use Ollama AI to generate a descriptive commit message based on your changes."
    ),
)
@click.option(
    "-i",
    "--interactive",
    is_flag=True,
    help=(
        "Enable interactive mode to review and edit the AI-generated commit "
        "message. Only works with --ollama."
    ),
)
@click.option(
    "-p",
    "--prompt-type",
    type=click.Choice(["simple", "advanced"], case_sensitive=False),
    default="advanced",
    help=(
        "Select AI prompt complexity for commit message generation. "
        "'simple' for basic messages, 'advanced' for detailed analysis."
    ),
    metavar="<type>",
)
# General Options Group
@click.option(
    "-nc",
    "--no-confirm",
    is_flag=True,
    help=(
        "Skip all confirmation prompts and proceed automatically with suggested values."
    ),
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help=(
        "Enable verbose output mode to show detailed debug information "
        "during execution."
    ),
)
def main(
    add: str | None,
    message: str | None,
    branch: str | None,
    ollama: bool,
    interactive: bool,
    no_confirm: bool,
    commit_type: str | None,
    verbose: bool,
    prompt_type: str,
) -> None:
    """Automate git add, commit, and push operations with smart features.

    This tool streamlines your git workflow by combining add, commit, and push
    operations with intelligent features like AI-powered commit messages and
    conventional commits support.

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
    """  # noqa: D301
    setup_signal_handlers()

    try:
        # Process -a argument (glob expansion)
        processed_files, _ = _process_add_argument(add)

        # Handle case where -a was provided but matched no files
        if processed_files == "":
            rprint(
                Panel(
                    "The -a argument resulted in no files to stage. Nothing to commit.",
                    title="No Files to Stage via -a",
                    border_style="yellow",
                )
            )
            sys.exit(0)

        # Build configuration
        config = GitConfig(
            files=processed_files if processed_files is not None else ".",
            message=message if not ollama else None,
            branch=branch,
            use_ollama=ollama,
            interactive=interactive,
            skip_confirmation=no_confirm,
            verbose=verbose,
            prompt_type=prompt_type.lower(),
        )

        # Create interaction layer and workflow
        interaction = RichQuestionaryInteraction()
        workflow = GitWorkflow(
            config,
            interaction,
            files_from_cli=(add is not None),
            commit_type_override=commit_type,
        )

        # Run workflow and exit with its return code
        exit_code = workflow.run()
        sys.exit(exit_code)

    except Exception as e:
        err = COLORS["error"]
        content = f"[{err}]Critical error:\n{e}[/{err}]\n\nSuggestion: "
        content += "Please check your git repository and configuration."
        rprint(Panel(content, title="Critical Error", border_style="red"))
        sys.exit(1)


if __name__ == "__main__":
    main()
