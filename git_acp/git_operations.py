"""Git operations module for git-acp package."""

import subprocess
from typing import Set, Tuple, List, Dict
from rich import print as rprint
from rich.console import Console
from collections import Counter
import json

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
    except Exception as e:
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

def get_recent_commits(num_commits: int = 10) -> List[Dict[str, str]]:
    """
    Get recent commit messages and metadata.
    
    Args:
        num_commits: Number of recent commits to retrieve
        
    Returns:
        List[Dict[str, str]]: List of commit dictionaries with 'hash', 'message', 
                             'author', and 'date' keys
        
    Raises:
        GitError: If unable to get commit history
    """
    try:
        format_str = "--pretty=format:%H%n%s%n%an%n%ad%n---%n"
        stdout, _ = run_git_command(["git", "log", "-n", str(num_commits), format_str])
        
        commits = []
        current_commit = {}
        
        for line in stdout.split('\n'):
            if line == "---":
                if current_commit:
                    commits.append(current_commit)
                    current_commit = {}
                continue
                
            if not current_commit:
                current_commit['hash'] = line
            elif 'message' not in current_commit:
                current_commit['message'] = line
            elif 'author' not in current_commit:
                current_commit['author'] = line
            elif 'date' not in current_commit:
                current_commit['date'] = line
        
        if current_commit:
            commits.append(current_commit)
            
        return commits
    except GitError as e:
        raise GitError(f"Failed to get commit history: {e}")

def analyze_commit_patterns() -> Dict[str, Counter]:
    """
    Analyze patterns in recent commits.
    
    Returns:
        Dict[str, Counter]: Dictionary containing frequency analysis of:
            - commit_types: Types of commits (feat, fix, etc.)
            - message_length: Typical message lengths
            - authors: Commit authors
            
    Raises:
        GitError: If unable to analyze commits
    """
    try:
        commits = get_recent_commits(50)  # Analyze last 50 commits
        
        patterns = {
            'commit_types': Counter(),
            'message_length': Counter(),
            'authors': Counter()
        }
        
        for commit in commits:
            # Analyze commit type
            message = commit['message']
            if ': ' in message:
                commit_type = message.split(': ')[0]
                patterns['commit_types'][commit_type] += 1
            
            # Analyze message length
            length_category = len(message) // 10 * 10  # Group by tens
            patterns['message_length'][length_category] += 1
            
            # Count author contributions
            patterns['authors'][commit['author']] += 1
        
        return patterns
    except GitError as e:
        raise GitError(f"Failed to analyze commit patterns: {e}")

def find_related_commits(diff_content: str, num_commits: int = 5, config = None) -> List[Dict[str, str]]:
    """
    Find commits related to the current changes.
    
    Args:
        diff_content: Content of the current diff
        num_commits: Maximum number of related commits to return
        config: Configuration object with verbose flag
        
    Returns:
        List[Dict[str, str]]: List of related commit dictionaries
        
    Raises:
        GitError: If unable to find related commits
    """
    try:
        # Get file paths from the diff
        files = set()
        for line in diff_content.split('\n'):
            if line.startswith('+++ b/') or line.startswith('--- a/'):
                file_path = line[6:]
                if file_path != '/dev/null':
                    files.add(file_path)
        
        if not files:
            return []
        
        # Find commits that modified these files
        related_commits = []
        for file_path in files:
            format_str = "--pretty=format:%H%n%s%n%an%n%ad%n---%n"
            stdout, _ = run_git_command([
                "git", "log", "-n", str(num_commits),
                "--follow", format_str, "--", file_path
            ])
            
            current_commit = {}
            for line in stdout.split('\n'):
                if line == "---":
                    if current_commit and len(current_commit) == 4:  # Make sure we have all fields
                        if current_commit not in related_commits:
                            related_commits.append(current_commit.copy())  # Use copy to avoid reference issues
                    current_commit = {}
                    continue
                    
                if not current_commit:
                    current_commit['hash'] = line
                elif 'message' not in current_commit:
                    current_commit['message'] = line
                elif 'author' not in current_commit:
                    current_commit['author'] = line
                elif 'date' not in current_commit:
                    current_commit['date'] = line
            
            # Handle the last commit if it wasn't followed by a separator
            if current_commit and len(current_commit) == 4 and current_commit not in related_commits:
                related_commits.append(current_commit.copy())
        
        # Only print debug info in verbose mode
        if config.verbose:
            rprint(f"[yellow]Debug - Related commits found: {json.dumps(related_commits, indent=2)}[/yellow]")
        
        return related_commits[:num_commits]
    except GitError as e:
        raise GitError(f"Failed to find related commits: {e}") 