#!/usr/bin/env python3

"""
Script Description: This script automates Git add, commit, and push actions with optional AI-generated commit messages using Ollama.
Author: elvee
Version: 0.5.0
License: MIT
Creation Date: 20/12/2024
Last Modified: 20/12/2024
"""

import subprocess
import sys
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import click
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
    """Configuration class for git operations."""
    files: str = "."
    message: str = "Automated commit"
    branch: Optional[str] = None
    use_ollama: bool = False
    skip_confirmation: bool = False

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
    """Get the name of the current git branch."""
    stdout, _ = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return stdout

def get_git_diff() -> str:
    """Get the git diff, checking both staged and unstaged changes."""
    # First try to get staged changes
    stdout, _ = run_git_command(["git", "diff", "--staged"])
    if stdout.strip():
        rprint("[yellow]Debug: Using staged changes diff[/yellow]")
        return stdout
    # If no staged changes, get unstaged changes
    rprint("[yellow]Debug: No staged changes, using unstaged diff[/yellow]")
    stdout, _ = run_git_command(["git", "diff"])
    return stdout

def generate_commit_message_with_ollama() -> str:
    """Generate a commit message using Ollama AI."""
    try:
        with console.status("[bold green]Generating commit message with Ollama..."):
            # Add files first so we can get the diff
            diff = get_git_diff()
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

def classify_commit_type(diff: str) -> CommitType:
    """
    Classify the commit type based on the git diff content.
    
    Args:
        diff: The git diff output
        
    Returns:
        CommitType: The classified commit type
    """
    # Debug: Print the first few lines of the diff
    rprint("[yellow]Debug: First 100 characters of diff:[/yellow]")
    rprint(diff[:100])
    
    # Debug: Print which patterns are matching
    def check_pattern(keywords: List[str], diff_text: str) -> bool:
        matches = [k for k in keywords if k in diff_text.lower()]
        if matches:
            rprint(f"[yellow]Debug: Matched keywords: {matches}[/yellow]")
        return bool(matches)

    # First check for documentation changes
    doc_keywords = ["docs/", ".md", "readme", "documentation", "license"]
    if check_pattern(doc_keywords, diff):
        rprint("[yellow]Debug: Classified as DOCS[/yellow]")
        return CommitType.DOCS

    # Then check for test changes
    test_keywords = ["test", ".test.", "spec", "_test", "test_"]
    if check_pattern(test_keywords, diff):
        rprint("[yellow]Debug: Classified as TEST[/yellow]")
        return CommitType.TEST

    # Check for style changes
    style_keywords = ["style", "format", "whitespace", "lint", "prettier", "eslint"]
    if check_pattern(style_keywords, diff):
        rprint("[yellow]Debug: Classified as STYLE[/yellow]")
        return CommitType.STYLE

    # Check for refactor
    refactor_keywords = ["refactor", "restructure", "cleanup", "clean up", "reorganize"]
    if check_pattern(refactor_keywords, diff):
        rprint("[yellow]Debug: Classified as REFACTOR[/yellow]")
        return CommitType.REFACTOR

    # Check for bug fixes
    fix_keywords = ["fix", "bug", "patch", "issue", "error", "crash", "problem", "resolve"]
    if check_pattern(fix_keywords, diff):
        rprint("[yellow]Debug: Classified as FIX[/yellow]")
        return CommitType.FIX

    # Check for reverts
    if "revert" in diff.lower():
        rprint("[yellow]Debug: Classified as REVERT[/yellow]")
        return CommitType.REVERT

    # Check for features
    feature_keywords = ["add", "new", "feature", "update", "introduce", 
                       "implement", "enhance", "create", "improve", "support"]
    if check_pattern(feature_keywords, diff):
        rprint("[yellow]Debug: Classified as FEAT[/yellow]")
        return CommitType.FEAT

    rprint("[yellow]Debug: Defaulting to CHORE[/yellow]")
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
    """Add files to git staging."""
    with console.status("[bold yellow]Adding files..."):
        run_git_command(["git", "add", files])
    rprint("[green]✓[/green] Files added successfully")

def git_commit(message: str) -> None:
    """Commit staged changes."""
    with console.status("[bold yellow]Committing changes..."):
        run_git_command(["git", "commit", "-m", message])
    rprint("[green]✓[/green] Changes committed successfully")

def git_push(branch: str) -> None:
    """Push changes to remote repository."""
    with console.status(f"[bold yellow]Pushing to {branch}..."):
        run_git_command(["git", "push", "origin", branch])
    rprint("[green]✓[/green] Changes pushed successfully")

@click.command()
@click.option('-a', '--add', default=".", help="Add specified file(s). Defaults to all changed files.")
@click.option('-m', '--message', help="Commit message. Defaults to 'Automated commit'.")
@click.option('-b', '--branch', help="Specify the branch to push to. Defaults to the current active branch.")
@click.option('-o', '--ollama', is_flag=True, help="Use Ollama AI to generate the commit message.")
@click.option('-nc', '--no-confirm', is_flag=True, help="Skip confirmation prompts.")
@click.option('-t', '--type', 'commit_type',
              type=click.Choice(['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'revert'],
                              case_sensitive=False),
              help="Override automatic commit type classification.")
def main(add: str, message: Optional[str], branch: Optional[str], 
         ollama: bool, no_confirm: bool, commit_type: Optional[str]) -> None:
    """
    Automate git add, commit, and push operations with optional AI-generated commit messages.
    """
    try:
        config = GitConfig(
            files=add,
            message=message or "Automated commit",
            branch=branch,
            use_ollama=ollama,
            skip_confirmation=no_confirm
        )

        if not config.branch:
            config.branch = get_current_branch()

        # Add files first
        git_add(config.files)

        if config.use_ollama:
            config.message = generate_commit_message_with_ollama()

        if not config.message:
            raise GitError("No commit message provided.")

        # Use provided commit type or classify automatically
        commit_type_enum = (CommitType.from_str(commit_type) if commit_type 
                          else classify_commit_type(get_git_diff()))
        formatted_message = format_commit_message(commit_type_enum, config.message)

        if not config.skip_confirmation:
            rprint(Panel.fit(
                formatted_message,
                title="[bold yellow]Commit Message[/bold yellow]",
                border_style="yellow"
            ))
            if not Confirm.ask("Do you want to proceed?"):
                rprint("[yellow]Operation cancelled.[/yellow]")
                return

        git_commit(formatted_message)
        git_push(config.branch)

        rprint("\n[bold green]🎉 All operations completed successfully![/bold green]")

    except GitError as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(1)

if __name__ == "__main__":
    main() 