"""Git operations module for git-acp package."""

import subprocess
from typing import Set, Tuple, List, Dict, Optional, Any
from collections import Counter
import json
from git_acp.formatting import (
    debug_header, debug_item, debug_json, debug_preview,
    status, success, warning
)

class GitError(Exception):
    """Custom exception for git-related errors."""
    pass

def run_git_command(command: list[str], config: Optional[Any] = None) -> Tuple[str, str]:
    """
    Run a git command and return its output.
    
    Args:
        command: List of command components
        config: Configuration object with verbose flag
    
    Returns:
        Tuple of (stdout, stderr)
        
    Raises:
        GitError: If the command fails
    """
    try:
        if config and config.verbose:
            debug_item("Running git command", ' '.join(command))
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise GitError(f"Command failed: {stderr}")
        if config and config.verbose and stdout.strip():
            debug_item("Command output", stdout.strip())
        return stdout.strip(), stderr.strip()
    except Exception as e:
        raise GitError(f"Failed to execute git command: {e}")

def get_current_branch(config: Optional[Any] = None) -> str:
    """
    Get the name of the current git branch.
    
    Args:
        config: Configuration object with verbose flag
    
    Returns:
        str: Name of the current branch
        
    Raises:
        GitError: If unable to determine current branch
    """
    stdout, _ = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], config)
    if config and config.verbose:
        debug_item("Current branch", stdout)
    return stdout

def git_add(files: str, config: Optional[Any] = None) -> None:
    """
    Add files to git staging area.
    
    Args:
        files: Space-separated list of files to add or "." for all files
        config: Configuration object with verbose flag
        
    Raises:
        GitError: If the git add operation fails
    """
    if config and config.verbose:
        debug_item("Adding files to staging area", files)
    with status("Adding files..."):
        run_git_command(["git", "add", files], config)
    success("Files added successfully")

def git_commit(message: str, config: Optional[Any] = None) -> None:
    """
    Commit staged changes to the repository.
    
    Args:
        message: The commit message
        config: Configuration object with verbose flag
        
    Raises:
        GitError: If the git commit operation fails
    """
    if config and config.verbose:
        debug_item("Committing with message", message)
    with status("Committing changes..."):
        run_git_command(["git", "commit", "-m", message], config)
    success("Changes committed successfully")

def git_push(branch: str, config: Optional[Any] = None) -> None:
    """
    Push committed changes to the remote repository.
    
    Args:
        branch: The name of the branch to push to
        config: Configuration object with verbose flag
        
    Raises:
        GitError: If the git push operation fails or remote is not accessible
    """
    if config and config.verbose:
        debug_item("Pushing to branch", branch)
    with status(f"Pushing to {branch}..."):
        run_git_command(["git", "push", "origin", branch], config)
    success("Changes pushed successfully")

def get_changed_files(config: Any) -> Set[str]:
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
    if config.verbose:
        debug_header("Getting changed files")
    
    # Get both staged and unstaged changes in porcelain format
    stdout_staged, _ = run_git_command(["git", "status", "--porcelain", "-uall"], config)
    
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
            debug_item("Processing line", line)
            debug_item("Extracted path", path)
            debug_item("Status", line[:2])
        
        return path
    
    # Process all status lines
    for line in stdout_staged.split('\n'):
        if path := process_status_line(line):
            files.add(path)
    
    if config.verbose:
        debug_item("Found files", str(files))
    
    return files

def unstage_files(config = None) -> None:
    """
    Unstage all staged changes.
    
    Args:
        config: Configuration object with verbose flag
    
    This function is typically called when an operation is cancelled or fails,
    to restore the git staging area to its previous state.
    
    Raises:
        GitError: If unable to unstage files
    """
    try:
        if config and config.verbose:
            debug_header("Unstaging all files")
        run_git_command(["git", "reset", "HEAD"], config)
    except GitError as e:
        warning(f"Failed to unstage changes: {e}")

def get_recent_commits(num_commits: int = 10, config = None) -> List[Dict[str, str]]:
    """
    Get recent commit messages and metadata.
    
    Args:
        num_commits: Number of recent commits to retrieve
        config: Configuration object with verbose flag
        
    Returns:
        List[Dict[str, str]]: List of commit dictionaries with 'hash', 'message', 
                             'author', and 'date' keys
        
    Raises:
        GitError: If unable to get commit history
    """
    try:
        if config and config.verbose:
            debug_item("Retrieving recent commits", str(num_commits))
        format_str = "--pretty=format:%H%n%s%n%an%n%ad%n---%n"
        stdout, _ = run_git_command(["git", "log", "-n", str(num_commits), format_str], config)
        
        commits = []
        current_commit = {}
        
        for line in stdout.split('\n'):
            if line == "---":
                if current_commit:
                    commits.append(current_commit)
                    if config and config.verbose:
                        debug_item("Found commit", json.dumps(current_commit))
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
            if config and config.verbose:
                debug_item("Found commit", json.dumps(current_commit))
            
        return commits
    except GitError as e:
        raise GitError(f"Failed to get commit history: {e}")

def analyze_commit_patterns(config = None) -> Dict[str, Counter]:
    """
    Analyze patterns in recent commits.
    
    Args:
        config: Configuration object with verbose flag
    
    Returns:
        Dict[str, Counter]: Dictionary containing frequency analysis of:
            - commit_types: Types of commits (feat, fix, etc.)
            - message_length: Typical message lengths
            - authors: Commit authors
            
    Raises:
        GitError: If unable to analyze commits
    """
    try:
        if config and config.verbose:
            debug_header("Analyzing commit patterns")
        commits = get_recent_commits(5, config)  # Analyze last 5 commits
        
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
                if config and config.verbose:
                    debug_item("Found commit type", commit_type)
            
            # Analyze message length
            length_category = len(message) // 10 * 10  # Group by tens
            patterns['message_length'][length_category] += 1
            
            # Count author contributions
            patterns['authors'][commit['author']] += 1
        
        if config and config.verbose:
            debug_header("Commit patterns:")
            debug_json(dict(patterns))
        
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
        if config and config.verbose:
            debug_header("Related commits found:")
            debug_json(related_commits)
        
        return related_commits[:num_commits]
    except GitError as e:
        raise GitError(f"Failed to find related commits: {e}") 