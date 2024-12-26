#!/usr/bin/env python3

"""
Git Add-Commit-Push (git-acp) automation tool.

This module provides a command-line interface for automating Git operations with enhanced features:
- Interactive file selection for staging
- AI-powered commit message generation using Ollama
- Smart commit type classification
- Conventional commits format support
- Rich terminal output with progress indicators

Author: elvee
Version: 0.8.0
License: MIT
Creation Date: 20-12-2024
Last Modified: 21-12-2024
"""

import subprocess
import sys
from typing import Optional, List, Tuple, Set, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
import click
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich import print as rprint

console = Console()

class CommitType(Enum):
    """Enum for commit types with their corresponding emojis."""
    FEAT = "feat ✨"
    FIX = "fix 🐛"
    DOCS = "docs 📝"
    STYLE = "style 💎"
    REFACTOR = "refactor ♻️"
    TEST = "test 🧪"
    CHORE = "chore 📦"
    REVERT = "revert ⏪"

    @classmethod
    def from_str(cls, type_str: str) -> 'CommitType':
        """Convert string to CommitType, case insensitive."""
        try:
            return cls[type_str.upper()]
        except KeyError:
            valid_types = [t.name.lower() for t in cls]
            raise GitError(
                f"Invalid commit type: {type_str}. "
                f"Valid types are: {', '.join(valid_types)}"
            )

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

class GitError(Exception):
    """Custom exception for git-related errors."""
    pass

def run_git_command(command: List[str]) -> Tuple[str, str]:
    """
    Run a git command and return its output.
    
    Args:
        command: List of command components
    
    Returns:
        Tuple of (stdout, stderr)
        
    Raises:
        GitError: If the command fails
    """
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise GitError(f"Command failed: {stderr}")
        return stdout.strip(), stderr.strip()
    except subprocess.SubprocessError as e:
        raise GitError(f"Failed to execute git command: {e}")

def get_current_branch() -> str:
    """
    Get the name of the current git branch.
    
    Returns:
        str: Name of the current branch
        
    Raises:
        GitError: If unable to determine current branch
    """
    stdout, _ = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return stdout

def debug_print(config: GitConfig, message: str) -> None:
    """
    Print debug message if verbose mode is enabled.
    
    Args:
        config: GitConfig instance containing configuration options
        message: Debug message to print
    """
    if config.verbose:
        rprint(f"[yellow]Debug: {message}[/yellow]")

def get_git_diff(config: GitConfig) -> str:
    """Get the git diff, checking both staged and unstaged changes."""
    # First try to get staged changes
    stdout, _ = run_git_command(["git", "diff", "--staged"])
    if stdout.strip():
        debug_print(config, "Using staged changes diff")
        return stdout
    # If no staged changes, get unstaged changes
    debug_print(config, "No staged changes, using unstaged diff")
    stdout, _ = run_git_command(["git", "diff"])
    return stdout

def generate_commit_message_with_ollama(config: GitConfig) -> str:
    """Generate a commit message using Ollama AI."""
    try:
        with console.status("[bold green]Generating commit message with Ollama..."):
            # Add files first so we can get the diff
            diff = get_git_diff(config)
            if not diff:
                raise GitError("No changes detected to generate commit message from.")
            
            process = subprocess.Popen(
                ["ollama", "run", "mevatron/diffsense:1.5b"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=diff)
            if process.returncode != 0:
                raise GitError(f"Ollama failed: {stderr}")
            return stdout.strip()
    except (subprocess.SubprocessError, GitError) as e:
        raise GitError(f"Failed to generate commit message: {e}")

def classify_commit_type(config: GitConfig, diff: str) -> CommitType:
    """
    Classify the commit type based on the git diff content.
    
    Args:
        config: GitConfig instance
        diff: The git diff output
        
    Returns:
        CommitType: The classified commit type
    """
    if config.verbose:
        debug_print(config, f"First 100 characters of diff:")
        rprint(diff[:100])
    
    def check_pattern(keywords: List[str], diff_text: str) -> bool:
        matches = [k for k in keywords if k in diff_text.lower()]
        if matches and config.verbose:
            debug_print(config, f"Matched keywords: {matches}")
        return bool(matches)

    # First check for documentation changes
    doc_keywords = ["docs/", ".md", "readme", "documentation", "license"]
    if check_pattern(doc_keywords, diff):
        debug_print(config, "Classified as DOCS")
        return CommitType.DOCS

    # Then check for test changes
    test_keywords = ["test", ".test.", "_test", "test_"]
    if check_pattern(test_keywords, diff):
        debug_print(config, "Classified as TEST")
        return CommitType.TEST

    # Check for style changes
    style_keywords = ["style", "format", "whitespace", "lint", "prettier", "eslint"]
    if check_pattern(style_keywords, diff):
        debug_print(config, "Classified as STYLE")
        return CommitType.STYLE

    # Check for refactor
    refactor_keywords = ["refactor", "restructure", "cleanup", "clean up", "reorganize"]
    if check_pattern(refactor_keywords, diff):
        debug_print(config, "Classified as REFACTOR")
        return CommitType.REFACTOR

    # Check for bug fixes
    fix_keywords = ["fix", "bug", "patch", "issue", "error", "crash", "problem", "resolve"]
    if check_pattern(fix_keywords, diff):
        debug_print(config, "Classified as FIX")
        return CommitType.FIX

    # Check for reverts
    if "revert" in diff.lower():
        debug_print(config, "Classified as REVERT")
        return CommitType.REVERT

    # Check for features
    feature_keywords = ["add", "new", "feature", "update", "introduce", 
                       "implement", "enhance", "create", "improve", "support"]
    if check_pattern(feature_keywords, diff):
        debug_print(config, "Classified as FEAT")
        return CommitType.FEAT

    debug_print(config, "Defaulting to CHORE")
    return CommitType.CHORE

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

def git_add(files: str) -> None:
    """
    Add files to git staging area.
    
    Args:
        files: Space-separated list of files to add or "." for all files
        
    Raises:
        GitError: If the git add operation fails
    """
    with console.status("[bold yellow]Adding files..."):
        run_git_command(["git", "add", files])
    rprint("[green]✓[/green] Files added successfully")

def git_commit(message: str) -> None:
    """
    Commit staged changes to the repository.
    
    Args:
        message: The commit message to use, formatted according to conventional commits
        
    Raises:
        GitError: If the git commit operation fails
    """
    with console.status("[bold yellow]Committing changes..."):
        run_git_command(["git", "commit", "-m", message])
    rprint("[green]✓[/green] Changes committed successfully")

def git_push(branch: str) -> None:
    """
    Push committed changes to the remote repository.
    
    Args:
        branch: The name of the branch to push to
        
    Raises:
        GitError: If the git push operation fails or remote is not accessible
    """
    with console.status(f"[bold yellow]Pushing to {branch}..."):
        run_git_command(["git", "push", "origin", branch])
    rprint("[green]✓[/green] Changes pushed successfully")

def get_changed_files(config: GitConfig) -> Set[str]:
    """
    Get list of changed files from git status.
    
    This function retrieves both staged and unstaged changes, excluding certain
    patterns like __pycache__ and compiled Python files.
    
    Args:
        config: GitConfig instance containing configuration options
        
    Returns:
        Set[str]: Set of file paths that have been modified
        
    Raises:
        GitError: If unable to get git status
    """
    # Get both staged and unstaged changes in porcelain format
    stdout_staged, _ = run_git_command(["git", "status", "--porcelain", "-uall"])
    
    files = set()
    exclude_patterns = ['__pycache__', '.pyc', '.pyo', '.pyd']
    
    def process_status_line(line: str) -> Optional[str]:
        """
        Process a single git status line and extract the filename.
        
        Args:
            line: A line from git status --porcelain output
            
        Returns:
            Optional[str]: The processed filename if valid, None otherwise
            
        Notes:
            The format of each line is: XY FILENAME
            where X is the status of the index and Y is the status of the working tree
        """
        if not line.strip():
            return None
            
        status = line[:2]
        if status == "??":
            return None
            
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            return None
            
        path = parts[1].strip()
        
        if " -> " in path:
            _, new_path = path.split(" -> ")
            path = new_path
            
        path = path.strip().strip('"')
        
        if any(pat in path for pat in exclude_patterns):
            return None
            
        if config.verbose:
            debug_print(config, f"Processing line: '{line}'")
            debug_print(config, f"Extracted path: '{path}'")
            debug_print(config, f"Status: '{status}'")
        
        return path
    
    # Process all status lines
    for line in stdout_staged.split('\n'):
        if path := process_status_line(line):
            files.add(path)
    
    if config.verbose:
        debug_print(config, f"Found files: {files}")
    
    return files

def unstage_files() -> None:
    """
    Unstage all staged changes.
    
    This function is typically called when an operation is cancelled or fails,
    to restore the git staging area to its previous state.
    
    Raises:
        GitError: If unable to unstage files
    """
    try:
        run_git_command(["git", "reset", "HEAD"])
        rprint("[yellow]Staged changes have been reset.[/yellow]")
    except GitError as e:
        rprint(f"[yellow]Warning: Failed to unstage changes: {e}[/yellow]")

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
                            else classify_commit_type(config, get_git_diff(config)))
            
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
            # Handle both CTRL+C and CTRL+D gracefully
            print()  # Add a newline for cleaner output
            rprint("[yellow]Operation cancelled by user.[/yellow]")
            sys.exit(0)  # Exit with success code since this is a user-initiated cancellation

    except GitError as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main(add=None, message=None, branch=None, ollama=False, no_confirm=False, commit_type=None, verbose=False) 