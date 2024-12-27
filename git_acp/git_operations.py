"""Git operations module for git-acp package."""

import subprocess
from typing import Set, Tuple
from rich import print as rprint
from rich.console import Console

console = Console()

class GitError(Exception):
    """Custom exception for git-related errors."""
    pass

def run_git_command(command: list[str]) -> Tuple[str, str]:
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
        message: The commit message
        
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

def get_changed_files(config) -> Set[str]:
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
    
    def process_status_line(line: str) -> str | None:
        """
        Process a single git status line and extract the filename.
        
        Args:
            line: A line from git status --porcelain output
            
        Returns:
            Optional[str]: The processed filename if valid, None otherwise
            
        Notes:
            The format of each line is: XY FILENAME
            where X is the status in the index and Y is the status in the working tree
        """
        if not line.strip():
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
            rprint(f"[yellow]Debug: Processing line: '{line}'[/yellow]")
            rprint(f"[yellow]Debug: Extracted path: '{path}'[/yellow]")
            rprint(f"[yellow]Debug: Status: '{line[:2]}'[/yellow]")
        
        return path
    
    # Process all status lines
    for line in stdout_staged.split('\n'):
        if path := process_status_line(line):
            files.add(path)
    
    if config.verbose:
        rprint(f"[yellow]Debug: Found files: {files}[/yellow]")
    
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
    except GitError as e:
        rprint(f"[yellow]Warning: Failed to unstage changes: {e}[/yellow]") 