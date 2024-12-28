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
from typing import Optional, List, Tuple, Set, Any, Union
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
from git_acp.ai_utils import generate_commit_message_with_ollama

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
        skip_confirmation: Whether to skip confirmation prompts.
        verbose: Whether to show debug information.
    """
    files: str = "."
    message: str = "Automated commit"
    branch: Optional[str] = None
    use_ollama: bool = False
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
        rprint(f"[yellow]Debug: {message}[/yellow]")

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

def select_files(files: Set[str]) -> str:
    """
    Present an interactive selection menu for changed files.
    
    Args:
        files: Set of changed files
        
    Returns:
        str: Space-separated list of selected files
    """
    if not files:
        raise GitError("No changed files found to commit.")
    
    if len(files) == 1:
        file = next(iter(files))
        rprint(f"[yellow]Adding file:[/yellow] {file}")
        return file
    
    # Sort files and ensure paths are properly displayed
    choices = sorted(list(files))
    
    # Add "All files" as the last option
    choices.append("All files")
    
    # Use a wider display for the checkbox prompt
    selected = questionary.checkbox(
        "Select files to commit (space to select, enter to confirm):",
        choices=choices,
        style=questionary.Style([
            ('qmark', 'fg:yellow bold'),
            ('question', 'bold'),
            ('pointer', 'fg:yellow bold'),
            ('highlighted', 'fg:yellow bold'),
            ('selected', 'fg:green'),
        ])
    ).ask()
    
    if not selected:
        raise GitError("No files selected.")
    
    if "All files" in selected:
        rprint("[yellow]Adding all files[/yellow]")
        return "."
        
    return " ".join(f'"{f}"' if ' ' in f else f for f in selected)

def select_commit_type(config: GitConfig, suggested_type: CommitType) -> CommitType:
    """
    Present an interactive selection menu for commit types.
    
    Args:
        config: GitConfig instance
        suggested_type: The automatically suggested commit type
        
    Returns:
        CommitType: The selected commit type
    """
    # Prepare choices with the suggested type first
    choices = []
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
            choices.insert(0, choice)  # Put suggested type at the top
        else:
            choices.append(choice)
    
    if config.verbose:
        debug_print(config, f"Suggested commit type: {suggested_type.value}")
    
    style = questionary.Style([
        ('qmark', 'fg:yellow bold'),
        ('question', 'bold'),
        ('pointer', 'fg:yellow bold'),
        ('highlighted', 'fg:yellow bold'),
        ('selected', 'fg:green bold'),
        ('answer', 'fg:green bold'),
        ('instruction', 'fg:yellow'),
        ('checkbox-selected', 'fg:green bold'),
    ])

    def validate_single_selection(selection: List[Any]) -> Union[bool, str]:
        """
        Validate that exactly one item is selected from a list.
        
        Args:
            selection: List of selected items
            
        Returns:
            Union[bool, str]: True if valid, error message string if invalid
        """
        if len(selection) != 1:
            return "Please select exactly one commit type"
        return True

    selected = questionary.checkbox(
        "Select commit type (space to select, enter to confirm):",
        choices=choices,
        style=style,
        instruction=" (suggested type in green)",
        validate=validate_single_selection
    ).ask()
    
    if not selected or len(selected) != 1:
        raise GitError("No commit type selected.")
        
    return selected[0]

@click.command()
@click.option('-a', '--add', help="Add specified file(s). If not specified, shows interactive file selection.")
@click.option('-m', '--message', help="Commit message. Defaults to 'Automated commit'.")
@click.option('-b', '--branch', help="Specify the branch to push to. Defaults to the current active branch.")
@click.option('-o', '--ollama', is_flag=True, help="Use Ollama AI to generate the commit message.")
@click.option('-nc', '--no-confirm', is_flag=True, help="Skip confirmation prompts.")
@click.option('-t', '--type', 'commit_type',
              type=click.Choice(['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'revert'],
                              case_sensitive=False),
              help="Override automatic commit type suggestion.")
@click.option('-v', '--verbose', is_flag=True, help="Show debug information.")
def main(add: Optional[str], message: Optional[str], branch: Optional[str],
         ollama: bool, no_confirm: bool, commit_type: Optional[str], verbose: bool) -> None:
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
                config.message = generate_commit_message_with_ollama(config)

            if not config.message:
                raise GitError("No commit message provided.")

            # Get suggested commit type
            suggested_type = (CommitType.from_str(commit_type) if commit_type 
                            else classify_commit_type(config))
            
            # Let user select commit type
            selected_type = select_commit_type(config, suggested_type)
            formatted_message = format_commit_message(selected_type, config.message)

            if not config.skip_confirmation:
                rprint(Panel.fit(
                    formatted_message,
                    title="[bold yellow]Commit Message[/bold yellow]",
                    border_style="yellow"
                ))
                if not Confirm.ask("Do you want to proceed?"):
                    unstage_files()
                    rprint("[yellow]Operation cancelled.[/yellow]")
                    return

            git_commit(formatted_message)
            git_push(config.branch)

            rprint("\n[bold green]🎉 All operations completed successfully![/bold green]")

        except (KeyboardInterrupt, EOFError, GitError) as e:
            # Unstage files before exiting
            unstage_files()
            if isinstance(e, GitError):
                raise
            # Handle user interruption
            rprint("[yellow]Operation cancelled by user.[/yellow]")
            sys.exit(0)  # Exit with success code since this is a user-initiated cancellation

    except GitError as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 