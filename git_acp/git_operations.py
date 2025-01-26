"""Git repository operations module.

This module provides functions for interacting with Git repositories, including:
- Running git commands
- Managing files (add, commit, push)
- Analyzing commit history
- Handling git operations errors
"""

import subprocess
import json
import shlex
from typing import Set, Tuple, List, Dict, Optional, Any, Literal
from git_acp.formatting import (
    debug_header, debug_item, debug_json, status, success, warning
)
from git_acp.constants import (
    EXCLUDED_PATTERNS,
    DEFAULT_REMOTE,
    DEFAULT_NUM_RECENT_COMMITS,
    COLORS
)
from rich.console import Console
from rich import print as rprint
from git_acp.types import GitConfig, OptionalConfig, DiffType

console = Console()

class GitError(Exception):
    """Custom exception for git-related errors."""

def run_git_command(
    command: list[str], 
    config: OptionalConfig = None
) -> Tuple[str, str]:
    """Execute a git command and return its output.

    Args:
        command: List of command components
        config: GitConfig instance containing configuration options
    
    Returns:
        Tuple[str, str]: A tuple containing (stdout, stderr)
        
    Raises:
        GitError: If the command fails or cannot be executed
    """
    try:
        if config and config.verbose:
            rprint(f"[{COLORS['debug_header']}]Running command:[/{COLORS['debug_header']}] {' '.join(command)}")
        
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
        raise GitError(f"Failed to execute git command: {e}") from e

def get_current_branch(config: OptionalConfig = None) -> str:
    """Get the name of the current git branch.
    
    Args:
        config: GitConfig instance containing configuration options
    
    Returns:
        str: Name of the current branch
        
    Raises:
        GitError: If unable to determine current branch
    """
    stdout, _ = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], config)
    if config and config.verbose:
        debug_item("Current branch", stdout)
    return stdout

def git_add(files: str, config: OptionalConfig = None) -> None:
    """Add files to git staging area.
    
    Args:
        files: Space-separated list of files to add or "." for all files
        config: GitConfig instance containing configuration options
        
    Raises:
        GitError: If the git add operation fails
    """
    if config and config.verbose:
        debug_item("Adding files to staging area", files)
    
    with status("Adding files..."):
        if files == ".":
            run_git_command(["git", "add", "."], config)
        else:
            # Split files by space, but preserve quoted strings
            file_list = shlex.split(files)
            for file in file_list:
                if config and config.verbose:
                    debug_item("Adding file", file)
                run_git_command(["git", "add", file], config)
    
    success("Files added successfully")

def git_commit(message: str, config: OptionalConfig = None) -> None:
    """Commit staged changes to the repository.
    
    Args:
        message: The commit message
        config: GitConfig instance containing configuration options
        
    Raises:
        GitError: If the git commit operation fails
    """
    if config and config.verbose:
        debug_item("Committing with message", message)
    
    with status("Committing changes..."):
        run_git_command(["git", "commit", "-m", message], config)
    success("Changes committed successfully")

def git_push(branch: str, config: OptionalConfig = None) -> None:
    """Push committed changes to the remote repository.
    
    Args:
        branch: The name of the branch to push to
        config: GitConfig instance containing configuration options
        
    Raises:
        GitError: If the git push operation fails or remote is not accessible
    """
    if config and config.verbose:
        debug_item("Pushing to branch", branch)
    
    with status(f"Pushing to {branch}..."):
        run_git_command(["git", "push", DEFAULT_REMOTE, branch], config)
    success("Changes pushed successfully")

def get_changed_files(config: OptionalConfig = None) -> Set[str]:
    """Get list of changed files from git status.
    
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

    stdout_staged, _ = run_git_command(["git", "status", "--porcelain", "-uall"], config)
    files = set()

    def process_status_line(line: str) -> Optional[str]:
        """Process a single git status line and extract the filename.
        
        The format of each line is: XY FILENAME
        where X is the status in the index and Y is the status in the working tree.
        
        Args:
            line: A line from git status --porcelain output
            
        Returns:
            Optional[str]: The processed filename if valid, None otherwise
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
        if any(pat in path for pat in EXCLUDED_PATTERNS):
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

def unstage_files(config: OptionalConfig = None) -> None:
    """Unstage all staged changes.
    
    This function is typically called when an operation is cancelled or fails,
    to restore the git staging area to its previous state.
    
    Args:
        config: GitConfig instance containing configuration options
    
    Raises:
        GitError: If unable to unstage files
    """
    try:
        if config and config.verbose:
            debug_header("Unstaging all files")
        run_git_command(["git", "reset", "HEAD"], config)
    except GitError as e:
        warning(f"Failed to unstage changes: {e}")

def get_recent_commits(
    num_commits: int = DEFAULT_NUM_RECENT_COMMITS,
    config: OptionalConfig = None
) -> List[Dict[str, str]]:
    """Get recent commit messages and metadata.
    
    Args:
        num_commits: Number of recent commits to retrieve
        config: GitConfig instance containing configuration options
        
    Returns:
        List[Dict[str, str]]: List of commit dictionaries with 'hash', 'message', 
                             'author', and 'date' keys
    """
    try:
        if config and config.verbose:
            debug_header("Getting recent commits")
            debug_item("Number of commits", str(num_commits))
        
        format_str = '%H%n%s%n%an%n%aI'  # hash, subject, author, ISO date
        stdout, _ = run_git_command([
            "git", "log",
            f"-{num_commits}",
            f"--pretty=format:{format_str}",
            "--no-merges"
        ], config)
        
        commits = []
        current_commit = {}
        
        for i, line in enumerate(stdout.split('\n')):
            if i % 4 == 0:
                if current_commit:
                    commits.append(current_commit)
                current_commit = {'hash': line}
            elif i % 4 == 1:
                current_commit['message'] = line
            elif i % 4 == 2:
                current_commit['author'] = line
            else:
                current_commit['date'] = line
        
        if current_commit:
            commits.append(current_commit)
            
        if config and config.verbose:
            debug_item("Found commits", str(len(commits)))
            
        return commits
        
    except Exception as e:
        raise GitError(f"Failed to get recent commits: {e}") from e

def find_related_commits(
    diff_content: str,
    num_commits: int = DEFAULT_NUM_RECENT_COMMITS,
    config: OptionalConfig = None
) -> List[Dict[str, str]]:
    """Find commits related to changes in the given diff content.

    Args:
        diff_content: The diff content to find related commits for
        num_commits: Maximum number of related commits to return
        config: GitConfig instance containing configuration options
        
    Returns:
        List[Dict[str, str]]: List of related commit dictionaries
        
    Raises:
        GitError: If unable to find related commits
    """
    try:
        # Get file paths from the diff
        files = {
            line[6:] for line in diff_content.split('\n')
            if (line.startswith('+++ b/') or line.startswith('--- a/'))
            and not line.endswith('/dev/null')
        }

        if not files:
            return []

        # Find commits that modified these files
        related_commits: List[Dict[str, str]] = []
        format_str = "--pretty=format:%H%n%s%n%an%n%ad%n---%n"

        for file_path in files:
            stdout, _ = run_git_command([
                "git", "log", "-n", str(num_commits),
                "--follow", format_str, "--", file_path
            ])

            current_commit: Dict[str, str] = {}
            for line in stdout.split('\n'):
                if line == "---":
                    if current_commit and len(current_commit) == 4:
                        if current_commit not in related_commits:
                            related_commits.append(current_commit.copy())
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

            if current_commit and len(current_commit) == 4 and current_commit not in related_commits:
                related_commits.append(current_commit.copy())

        if config and config.verbose:
            debug_header("Related commits found:")
            debug_json(related_commits)

        return related_commits[:num_commits]
        
    except GitError as e:
        raise GitError(f"Failed to find related commits: {e}") from e

def get_diff(diff_type: DiffType = "staged", config: OptionalConfig = None) -> str:
    """Get the git diff output for staged or unstaged changes.
    
    Args:
        diff_type: Type of diff to get ("staged" or "unstaged")
        config: GitConfig instance containing configuration options
        
    Returns:
        str: The git diff output
        
    Raises:
        GitError: If unable to get diff
    """
    try:
        if config and config.verbose:
            debug_header(f"Getting {diff_type} diff")
        
        if diff_type == "staged":
            stdout, _ = run_git_command(["git", "diff", "--staged"], config)
        else:
            stdout, _ = run_git_command(["git", "diff"], config)
            
        if config and config.verbose:
            debug_item("Diff length", str(len(stdout)))
            
        return stdout
        
    except GitError as e:
        raise GitError(f"Failed to get {diff_type} diff: {e}") from e

def create_branch(branch_name: str, config: OptionalConfig = None) -> None:
    """Create a new git branch.
    
    Args:
        branch_name: Name of the branch to create
        config: GitConfig instance containing configuration options
        
    Raises:
        GitError: If unable to create branch
    """
    try:
        if config and config.verbose:
            debug_item("Creating branch", branch_name)
            
        run_git_command(["git", "checkout", "-b", branch_name], config)
        success(f"Created and switched to branch '{branch_name}'")
        
    except GitError as e:
        raise GitError(f"Failed to create branch: {e}") from e

def delete_branch(branch_name: str, force: bool = False, config: OptionalConfig = None) -> None:
    """Delete a git branch.
    
    Args:
        branch_name: Name of the branch to delete
        force: Whether to force delete the branch
        config: GitConfig instance containing configuration options
        
    Raises:
        GitError: If unable to delete branch
    """
    try:
        if config and config.verbose:
            debug_item("Deleting branch", branch_name)
            
        cmd = ["git", "branch", "-D" if force else "-d", branch_name]
        run_git_command(cmd, config)
        success(f"Deleted branch '{branch_name}'")
        
    except GitError as e:
        raise GitError(f"Failed to delete branch: {e}") from e

def merge_branch(source_branch: str, config: OptionalConfig = None) -> None:
    """Merge a branch into the current branch.
    
    Args:
        source_branch: Name of the branch to merge from
        config: GitConfig instance containing configuration options
        
    Raises:
        GitError: If unable to merge branch
    """
    try:
        if config and config.verbose:
            debug_item("Merging branch", source_branch)
            
        run_git_command(["git", "merge", source_branch], config)
        success(f"Merged '{source_branch}' into current branch")
        
    except GitError as e:
        raise GitError(f"Failed to merge branch: {e}") from e

def manage_remote(
    operation: Literal["add", "remove", "set-url"],
    remote_name: str,
    url: Optional[str] = None,
    config: OptionalConfig = None
) -> None:
    """Manage git remotes.
    
    Args:
        operation: Type of remote operation
        remote_name: Name of the remote
        url: URL for the remote (required for add and set-url)
        config: GitConfig instance containing configuration options
        
    Raises:
        GitError: If unable to manage remote
    """
    try:
        if config and config.verbose:
            debug_item(f"Remote operation: {operation}", f"{remote_name} {url or ''}")
            
        if operation == "remove":
            run_git_command(["git", "remote", "remove", remote_name], config)
        elif url:
            if operation == "add":
                run_git_command(["git", "remote", "add", remote_name, url], config)
            else:  # set-url
                run_git_command(["git", "remote", "set-url", remote_name, url], config)
        success(f"Remote operation '{operation}' completed successfully")
        
    except GitError as e:
        raise GitError(f"Failed to {operation} remote: {e}") from e

def manage_tags(
    operation: Literal["create", "delete", "push"],
    tag_name: str,
    message: Optional[str] = None,
    config: OptionalConfig = None
) -> None:
    """Manage git tags.
    
    Args:
        operation: Type of tag operation
        tag_name: Name of the tag
        message: Tag message (for create operation)
        config: GitConfig instance containing configuration options
        
    Raises:
        GitError: If unable to manage tag
    """
    try:
        if config and config.verbose:
            debug_item(f"Tag operation: {operation}", tag_name)
            
        if operation == "create":
            cmd = ["git", "tag", "-a", tag_name, "-m", message or tag_name]
            run_git_command(cmd, config)
        elif operation == "delete":
            run_git_command(["git", "tag", "-d", tag_name], config)
        else:  # push
            run_git_command(["git", "push", DEFAULT_REMOTE, tag_name], config)
        success(f"Tag operation '{operation}' completed successfully")
        
    except GitError as e:
        raise GitError(f"Failed to {operation} tag: {e}") from e

def manage_stash(
    operation: Literal["save", "pop", "apply", "drop", "list"],
    message: Optional[str] = None,
    stash_id: Optional[str] = None,
    config: OptionalConfig = None
) -> Optional[str]:
    """Manage git stash operations.
    
    Args:
        operation: Type of stash operation
        message: Stash message (for save operation)
        stash_id: Stash identifier (for pop, apply, drop operations)
        config: GitConfig instance containing configuration options
        
    Returns:
        Optional[str]: Stash list output for list operation
        
    Raises:
        GitError: If unable to manage stash
    """
    try:
        if config and config.verbose:
            debug_item(f"Stash operation: {operation}", f"{message or ''} {stash_id or ''}")
            
        if operation == "save":
            cmd = ["git", "stash", "push", "-m", message] if message else ["git", "stash"]
            run_git_command(cmd, config)
        elif operation == "list":
            stdout, _ = run_git_command(["git", "stash", "list"], config)
            return stdout
        else:
            cmd = ["git", "stash", operation]
            if stash_id:
                cmd.append(stash_id)
            run_git_command(cmd, config)
            
        if operation != "list":
            success(f"Stash operation '{operation}' completed successfully")
        return None
        
    except GitError as e:
        raise GitError(f"Failed to {operation} stash: {e}") from e
