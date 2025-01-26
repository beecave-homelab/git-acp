#!/usr/bin/env python3

"""
Git Add-Commit-Push (git-acp) automation tool.

This module provides a command-line interface for automating Git operations with enhanced features:
- Interactive file selection for staging
- AI-powered commit message generation using Ollama
- Smart commit type classification
- Conventional commits format support
- Rich terminal output with progress indicators
"""

import subprocess
import sys
from typing import List, Set, Union, Optional
from dataclasses import dataclass
from enum import Enum
import click
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich import print as rprint

from git_acp.git_operations import (
    GitError, run_git_command, get_current_branch, git_add,
    git_commit, git_push, get_changed_files, unstage_files
)
from git_acp.classification import CommitType, classify_commit_type
from git_acp.ai_utils import generate_commit_message_with_ai
from git_acp.constants import COLORS, QUESTIONARY_STYLE
from git_acp.types import OptionalConfig

console = Console()

@dataclass
class GitConfig:
    """
    Configuration class for git operations.
    
    Attributes:
        files: Files to be added to git staging. Defaults to "." for all files.
        message: Commit message to use. Defaults to "Automated commit".
        branch: Target branch for push operation. If None, uses current branch.
        use_ollama: Whether to use Ollama AI for commit message generation.
        interactive: Whether to allow editing of AI-generated commit messages.
        skip_confirmation: Whether to skip confirmation prompts.
        verbose: Whether to show debug information.
    """
    files: str = "."
    message: str = "Automated commit"
    branch: OptionalConfig = None
    use_ollama: bool = False
    interactive: bool = False
    skip_confirmation: bool = False
    verbose: bool = False

def debug_print(config: GitConfig, message: str) -> None:
    """
    Print debug message if verbose mode is enabled.
    
    Args:
        config: GitConfig instance containing configuration options
        message: Debug message to print
    """
    if config.verbose:
        rprint(f"[{COLORS['warning']}]Debug: {message}[/{COLORS['warning']}]")

def format_commit_message(commit_type: CommitType, message: str) -> str:
    """
    Format the commit message according to the conventional commits specification.
    
    Args:
        commit_type: The type of commit
        message: The commit message
        
    Returns:
        str: The formatted commit message
    """
    lines = message.split('\n')
    title = lines[0]
    description = '\n'.join(lines[1:])
    return f"{commit_type.value}: {title}\n\n{description}".strip()

def select_files(changed_files: Set[str]) -> str:
    """
    Present an interactive selection menu for changed files.
    
    Args:
        changed_files: Set of files with uncommitted changes
        
    Returns:
        str: Space-separated list of selected files, with proper quoting
    """
    if not changed_files:
        raise GitError("No changed files found to commit.")
    
    if len(changed_files) == 1:
        selected_file = next(iter(changed_files))
        rprint(f"[{COLORS['warning']}]Adding file:[/{COLORS['warning']}] {selected_file}")
        return f'"{selected_file}"' if ' ' in selected_file else selected_file
    
    # Sort files and ensure paths are properly displayed
    file_choices = sorted(list(changed_files))
    
    # Add "All files" as the last option
    file_choices.append("All files")
    
    # Use a wider display for the checkbox prompt
    selected_files = questionary.checkbox(
        "Select files to commit (space to select, enter to confirm):",
        choices=file_choices,
        style=questionary.Style(QUESTIONARY_STYLE)
    ).ask()
    
    if not selected_files:
        raise GitError("No files selected.")
    
    if "All files" in selected_files:
        rprint(f"[{COLORS['warning']}]Adding all files[/{COLORS['warning']}]")
        return "."
    
    # Print selected files for user feedback
    rprint(f"[{COLORS['warning']}]Adding files:[/{COLORS['warning']}]")
    for file in selected_files:
        rprint(f"  - {file}")
    
    # Return files as a space-separated string, properly quoted if needed
    return " ".join(f'"{f}"' if ' ' in f else f for f in selected_files)

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
    if config.skip_confirmation or suggested_type.value in ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'revert']:
        if config.verbose:
            debug_print(config, f"Auto-selecting commit type: {suggested_type.value}")
        return suggested_type

    # Create choices list with suggested type highlighted
    commit_type_choices = []
    for commit_type in CommitType:
        # Add (suggested) tag for the suggested type
        name = (f"{commit_type.value} (suggested)" 
               if commit_type == suggested_type 
               else commit_type.value)
        choice = {
            'name': name,
            'value': commit_type,
            'checked': False  # Don't pre-select any option
        }
        if commit_type == suggested_type:
            commit_type_choices.insert(0, choice)  # Put suggested type at the top
        else:
            commit_type_choices.append(choice)
    
    if config.verbose:
        debug_print(config, f"Suggested commit type: {suggested_type.value}")

    def validate_single_selection(selected_types: List[CommitType]) -> Union[bool, str]:
        """
        Validate that exactly one commit type is selected.
        
        Args:
            selected_types: List of selected commit types
            
        Returns:
            Union[bool, str]: True if valid, error message string if invalid
        """
        if len(selected_types) != 1:
            return "Please select exactly one commit type"
        return True

    selected_types = questionary.checkbox(
        "Select commit type (space to select, enter to confirm):",
        choices=commit_type_choices,
        style=questionary.Style(QUESTIONARY_STYLE),
        instruction=" (suggested type marked)",
        validate=validate_single_selection
    ).ask()
    
    if not selected_types or len(selected_types) != 1:
        raise GitError("No commit type selected.")
        
    return selected_types[0]

@click.command()
@click.option('-a', '--add', help="Add specified file(s). If not specified, shows interactive file selection.")
@click.option('-m', '--message', help="Commit message. Defaults to 'Automated commit'.")
@click.option('-b', '--branch', help="Specify the branch to push to. Defaults to the current active branch.")
@click.option('-o', '--ollama', is_flag=True, help="Use Ollama AI to generate the commit message.")
@click.option('-i', '--interactive', is_flag=True, help="Allow editing of AI-generated commit message (requires --ollama).")
@click.option('-nc', '--no-confirm', is_flag=True, help="Skip confirmation prompts.")
@click.option('-t', '--type', 'commit_type',
              type=click.Choice(['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'revert'],
                              case_sensitive=False),
              help="Override automatic commit type suggestion.")
@click.option('-v', '--verbose', is_flag=True, help="Show debug information.")
def main(add: Optional[str], message: Optional[str], branch: Optional[str],
         ollama: bool, interactive: bool, no_confirm: bool, commit_type: Optional[str], verbose: bool) -> None:
    """
    Automate git add, commit, and push operations with optional AI-generated commit messages.
    """
    try:
        # If no files specified, show interactive selection
        config = GitConfig(
            files=add or ".",
            message=message or "Automated commit",
            branch=branch,
            use_ollama=ollama,
            interactive=interactive,
            skip_confirmation=no_confirm,
            verbose=verbose
        )

        if add is None:
            changed_files = get_changed_files(config)
            if not changed_files:
                raise GitError("No changes detected in the repository.")
            config.files = select_files(changed_files)

        if not config.branch:
            config.branch = get_current_branch()

        # Add files first
        git_add(config.files)

        try:
            if config.use_ollama:
                config.message = generate_commit_message_with_ai(config)

            if not config.message:
                raise GitError("No commit message provided.")

            # Get suggested commit type
            suggested_type = (CommitType.from_str(commit_type) if commit_type 
                            else classify_commit_type(config))
            
            # Let user select commit type, unless it was specified with -t flag
            rprint(f"[{COLORS['bold']}]🤖 Analyzing changes to suggest commit type...[/{COLORS['bold']}]")
            if commit_type:
                selected_type = suggested_type
                rprint(f"[{COLORS['success']}]✓ Using specified commit type: {selected_type.value}[/{COLORS['success']}]")
            else:
                selected_type = select_commit_type(config, suggested_type)
                rprint(f"[{COLORS['success']}]✓ Commit type selected successfully[/{COLORS['success']}]")
            formatted_message = format_commit_message(selected_type, config.message)

            if not config.skip_confirmation:
                rprint(Panel.fit(
                    formatted_message,
                    title=f"[{COLORS['ai_message_header']}]Commit Message[/{COLORS['ai_message_header']}]",
                    border_style=COLORS['ai_message_border']
                ))
                if not Confirm.ask("Do you want to proceed?"):
                    unstage_files()
                    raise GitError("Operation cancelled by user.")
            else:
                rprint(Panel.fit(
                    formatted_message,
                    title=f"[{COLORS['ai_message_header']}]Auto-committing with message[/{COLORS['ai_message_header']}]",
                    border_style=COLORS['ai_message_border']
                ))

            git_commit(formatted_message)
            git_push(config.branch)

            rprint(f"\n[{COLORS['success']}]🎉 All operations completed successfully![/{COLORS['success']}]")

        except (KeyboardInterrupt, EOFError, GitError) as e:
            # Unstage files before exiting
            unstage_files()
            if isinstance(e, GitError):
                raise
            # Handle user interruption
            rprint(f"[{COLORS['warning']}]Operation cancelled by user.[/{COLORS['warning']}]")
            sys.exit(0)  # Exit with success code since this is a user-initiated cancellation

    except GitError as e:
        rprint(f"[{COLORS['error']}]Error:[/{COLORS['error']}] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 