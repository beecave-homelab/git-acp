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
import signal
import sys
from typing import Set, Tuple, List, Dict, Optional, Any, Literal
from git_acp.utils import (
    debug_header, debug_item, debug_json, status, success, warning,
    GitConfig, OptionalConfig, DiffType
)
from git_acp.config import (
    EXCLUDED_PATTERNS,
    DEFAULT_REMOTE,
    DEFAULT_NUM_RECENT_COMMITS,
    COLORS
)
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint
from collections import Counter

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
            debug_header("Git Command Execution")
            debug_item("Command", ' '.join(command))
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            if config and config.verbose:
                debug_header("Git Command Failed")
                debug_item("Command", ' '.join(command))
                debug_item("Exit Code", str(process.returncode))
                debug_item("Error Output", stderr.strip())
            
            # Common git error patterns with user-friendly messages
            error_patterns = {
                "not a git repository": "Not a git repository. Please run this command in a git repository.",
                "did not match any files": "No files matched the specified pattern. Please check the file paths.",
                "nothing to commit": "No changes to commit. Working directory is clean.",
                "permission denied": "Permission denied. Please check your repository permissions.",
                "remote: Repository not found": "Remote repository not found. Please check the repository URL and your access rights.",
                "failed to push": "Failed to push changes. Please pull the latest changes and resolve any conflicts.",
                "cannot lock ref": "Cannot lock ref. Another git process may be running.",
                "refusing to merge unrelated histories": "Cannot merge unrelated histories. Use --allow-unrelated-histories if intended.",
                "error: your local changes would be overwritten": "Local changes would be overwritten. Please commit or stash them first."
            }
            
            for pattern, message in error_patterns.items():
                if pattern in stderr.lower():
                    raise GitError(message)
            
            # If no specific pattern matches, provide a generic error message
            raise GitError(f"Git command failed: {stderr.strip()}")
            
        if config and config.verbose and stdout.strip():
            debug_item("Command Output", stdout.strip())
            
        return stdout.strip(), stderr.strip()
        
    except FileNotFoundError:
        if config and config.verbose:
            debug_header("Git Command Error")
            debug_item("Error Type", "FileNotFoundError")
        raise GitError("Git is not installed or not in PATH. Please install git and try again.")
    except PermissionError:
        if config and config.verbose:
            debug_header("Git Command Error")
            debug_item("Error Type", "PermissionError")
            debug_item("Command", ' '.join(command))
        raise GitError("Permission denied while executing git command. Please check your permissions.")
    except Exception as e:
        if config and config.verbose:
            debug_header("Git Command Error")
            debug_item("Error Type", e.__class__.__name__)
            debug_item("Error Message", str(e))
            debug_item("Command", ' '.join(command))
        raise GitError(f"Failed to execute git command: {str(e)}") from e

def get_current_branch(config: OptionalConfig = None) -> str:
    """Get the name of the current git branch.
    
    Args:
        config: GitConfig instance containing configuration options
    
    Returns:
        str: Name of the current branch
        
    Raises:
        GitError: If unable to determine current branch
    """
    try:
        if config and config.verbose:
            debug_header("Getting Current Branch")
        stdout, _ = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], config)
        if not stdout:
            raise GitError("Failed to determine current branch. Are you in a valid git repository?")
        if config and config.verbose:
            debug_item("Current Branch", stdout)
        return stdout
    except GitError as e:
        if config and config.verbose:
            debug_header("Branch Detection Failed")
            debug_item("Error", str(e))
        raise GitError("Could not determine the current branch. Please ensure you're in a git repository.") from e

def git_add(files: str, config: OptionalConfig = None) -> None:
    """Add files to git staging area.
    
    Args:
        files: Space-separated list of files to add or "." for all files
        config: GitConfig instance containing configuration options
        
    Raises:
        GitError: If the git add operation fails
    """
    try:
        if config and config.verbose:
            debug_header("Adding Files to Staging Area")
            debug_item("Raw files input", files)
        
        with status("Adding files..."):
            if files == ".":
                if config and config.verbose:
                    debug_item("Adding all files", ".")
                run_git_command(["git", "add", "."], config)
            else:
                # Split files by space, but preserve quoted strings
                file_list = shlex.split(files)
                if config and config.verbose:
                    debug_item("Parsed file list", str(file_list))
                for file in file_list:
                    if config and config.verbose:
                        debug_item("Adding file", file)
                        debug_item("Git command", f"git add {file}")
                    run_git_command(["git", "add", file], config)
        
        success("Files added successfully")
    except GitError as e:
        if config and config.verbose:
            debug_header("Git Add Failed")
            debug_item("Error", str(e))
            debug_item("Files", files)
            debug_item("Command", "git add " + files)
        raise GitError(f"Failed to add files to staging area: {str(e)}") from e

def git_commit(message: str, config: OptionalConfig = None) -> None:
    """Commit staged changes to the repository.
    
    Args:
        message: The commit message
        config: GitConfig instance containing configuration options
        
    Raises:
        GitError: If the git commit operation fails
    """
    try:
        if config and config.verbose:
            debug_header("Committing Changes")
            debug_item("Message", message)
        
        with status("Committing changes..."):
            run_git_command(["git", "commit", "-m", message], config)
        success("Changes committed successfully")
    except GitError as e:
        if config and config.verbose:
            debug_header("Commit Failed")
            debug_item("Error", str(e))
        raise GitError(f"Failed to commit changes: {str(e)}") from e

def git_push(branch: str, config: OptionalConfig = None) -> None:
    """Push committed changes to the remote repository.
    
    Args:
        branch: The name of the branch to push to
        config: GitConfig instance containing configuration options
        
    Raises:
        GitError: If the git push operation fails or remote is not accessible
    """
    try:
        if config and config.verbose:
            debug_header("Pushing Changes")
            debug_item("Branch", branch)
            debug_item("Remote", DEFAULT_REMOTE)
        
        with status(f"Pushing to {branch}..."):
            run_git_command(["git", "push", DEFAULT_REMOTE, branch], config)
        success("Changes pushed successfully")
    except GitError as e:
        if config and config.verbose:
            debug_header("Push Failed")
            debug_item("Error", str(e))
            debug_item("Branch", branch)
            debug_item("Remote", DEFAULT_REMOTE)
        
        if "rejected" in str(e).lower():
            raise GitError(f"Push rejected. Please pull the latest changes first: git pull {DEFAULT_REMOTE} {branch}") from e
        elif "no upstream branch" in str(e).lower():
            raise GitError(f"No upstream branch. Set the remote with: git push --set-upstream {DEFAULT_REMOTE} {branch}") from e
        else:
            raise GitError(f"Failed to push changes: {str(e)}") from e

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
    if config and config.verbose:
        debug_header("Getting changed files")

    stdout_staged, _ = run_git_command(["git", "status", "--porcelain", "-uall"], config)
    if config and config.verbose:
        debug_item("Raw git status output", stdout_staged)
    
    files = set()

    def process_status_line(line: str) -> Optional[str]:
        """Process a single git status line and extract the filename.
        
        The format of each line is: XY FILENAME
        where X is the status in the index and Y is the status in the working tree.
        
        Args:
            line: A line from git status --porcelain output
            
        Returns:
            Optional[str]: The extracted file path, or None if it should be excluded
        """
        if not line.strip():
            return None
            
        if config and config.verbose:
            debug_item("Processing status line", line)
            
        # Extract the path, handling renames
        if " -> " in line:
            path = line.split(" -> ")[-1].strip()
        else:
            # The first two characters are the status codes
            status_codes = line[:2]
            # Find the actual start of the filename after the status codes
            # This preserves leading dots and spaces in filenames
            path = line[2:].lstrip()  # Remove only leading spaces after status codes
            
        if config and config.verbose:
            debug_item("Status codes", status_codes)
            debug_item("Extracted path", path)
            
        # Check if the file should be excluded
        for pattern in EXCLUDED_PATTERNS:
            if pattern in path:
                if config and config.verbose:
                    debug_item("Excluded path", f"Pattern '{pattern}' matched '{path}'")
                return None
                
        return path
        
    # Process each line of the status output
    for line in stdout_staged.splitlines():
        path = process_status_line(line)
        if path:
            if config and config.verbose:
                debug_item("Adding path to set", path)
            files.add(path)
            
    if config and config.verbose:
        debug_item("Final file set", str(files))
        
    return files

def unstage_files(config: OptionalConfig = None) -> None:
    """Unstage all files from the staging area.
    
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
        raise GitError(f"Failed to unstage files: {str(e)}") from e

def get_recent_commits(
    num_commits: int = DEFAULT_NUM_RECENT_COMMITS,
    config: OptionalConfig = None
) -> List[Dict[str, str]]:
    """Get recent commit history.
    
    Args:
        num_commits: Number of recent commits to fetch
        config: GitConfig instance containing configuration options
        
    Returns:
        List[Dict[str, str]]: List of commit dictionaries with hash, message, author, date
        
    Raises:
        GitError: If unable to get commit history
    """
    try:
        if config and config.verbose:
            debug_header("Getting recent commits")
            debug_item("Number of commits", str(num_commits))
        
        # Get commit history in JSON format
        stdout, _ = run_git_command([
            "git", "log",
            f"-{num_commits}",
            "--pretty=format:{\"hash\":\"%h\",\"message\":\"%s\",\"author\":\"%an\",\"date\":\"%ad\"}",
            "--date=short"
        ], config)
        
        if not stdout:
            return []
            
        # Parse each line as a JSON object
        commits = []
        for line in stdout.splitlines():
            try:
                commit = json.loads(line)
                commits.append(commit)
            except json.JSONDecodeError:
                continue
                
        if config and config.verbose:
            debug_item("Found commits", str(len(commits)))
            
        return commits
        
    except GitError as e:
        raise GitError(f"Failed to get recent commits: {str(e)}") from e

def find_related_commits(
    diff_content: str,
    num_commits: int = DEFAULT_NUM_RECENT_COMMITS,
    config: OptionalConfig = None
) -> List[Dict[str, str]]:
    """Find commits related to the current changes.
    
    This function searches the commit history for commits that modified
    similar files or areas of code.
    
    Args:
        diff_content: The git diff content to analyze
        num_commits: Maximum number of related commits to find
        config: GitConfig instance containing configuration options
        
    Returns:
        List[Dict[str, str]]: List of related commit dictionaries
        
    Raises:
        GitError: If unable to find related commits
    """
    try:
        # Get all recent commits first
        all_commits = get_recent_commits(num_commits * 2, config)  # Get more commits to filter from
        related_commits = []
        
        # Extract file paths from the current diff
        current_files = set()
        for line in diff_content.splitlines():
            if line.startswith("+++ b/") or line.startswith("--- a/"):
                file_path = line[6:]  # Remove "+++ b/" or "--- a/"
                if file_path != "/dev/null":  # Ignore deleted files
                    current_files.add(file_path)
        
        # Find commits that modified the same files
        for commit in all_commits:
            try:
                # Get the diff for this commit
                stdout, _ = run_git_command([
                    "git", "show",
                    "--name-only",
                    "--pretty=format:",  # Empty format to only get file names
                    commit["hash"]
                ], config)
                
                # Check if any of the files match
                commit_files = set(stdout.splitlines())
                if current_files & commit_files:  # If there's any intersection
                    related_commits.append(commit)
                    if len(related_commits) >= num_commits:
                        break
                        
            except GitError:
                continue  # Skip commits that can't be analyzed
        
        if config and config.verbose:
            debug_header("Related commits found:")
            for commit in related_commits:
                debug_json(commit)
        
        return related_commits
        
    except GitError as e:
        raise GitError(f"Failed to find related commits: {str(e)}") from e

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
        raise GitError(f"Failed to get {diff_type} diff: {str(e)}") from e

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
            debug_header("Creating branch")
            debug_item("Creating branch", branch_name)
        run_git_command(["git", "checkout", "-b", branch_name], config)
    except GitError as e:
        raise GitError(f"Failed to create branch: {str(e)}") from e

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
            debug_header("Deleting branch")
            debug_item("Deleting branch", branch_name)
        if force:
            run_git_command(["git", "branch", "-D", branch_name], config)
        else:
            run_git_command(["git", "branch", "-d", branch_name], config)
    except GitError as e:
        raise GitError(f"Failed to delete branch: {str(e)}") from e

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
            debug_header("Merging branch")
            debug_item("Merging branch", source_branch)
        run_git_command(["git", "merge", source_branch], config)
    except GitError as e:
        raise GitError(f"Failed to merge branch: {str(e)}") from e

def manage_remote(
    operation: Literal["add", "remove", "set-url"],
    remote_name: str,
    url: Optional[str] = None,
    config: OptionalConfig = None
) -> None:
    """Manage git remotes (add, remove, set-url).
    
    Args:
        operation: The operation to perform
        remote_name: Name of the remote
        url: URL for the remote (required for add and set-url)
        config: GitConfig instance containing configuration options
        
    Raises:
        GitError: If the remote operation fails
    """
    try:
        if config and config.verbose:
            debug_item(f"Remote operation: {operation}", f"{remote_name} {url or ''}")
        
        if operation == "add":
            if not url:
                raise GitError("URL is required for adding a remote")
            run_git_command(["git", "remote", "add", remote_name, url], config)
        elif operation == "remove":
            run_git_command(["git", "remote", "remove", remote_name], config)
        elif operation == "set-url":
            if not url:
                raise GitError("URL is required for setting remote URL")
            run_git_command(["git", "remote", "set-url", remote_name, url], config)
    except GitError as e:
        raise GitError(f"Failed to {operation} remote: {str(e)}") from e

def manage_tags(
    operation: Literal["create", "delete", "push"],
    tag_name: str,
    message: Optional[str] = None,
    config: OptionalConfig = None
) -> None:
    """Manage git tags (create, delete, push).
    
    Args:
        operation: The operation to perform
        tag_name: Name of the tag
        message: Tag message (for create operation)
        config: GitConfig instance containing configuration options
        
    Raises:
        GitError: If the tag operation fails
    """
    try:
        if config and config.verbose:
            debug_item(f"Tag operation: {operation}", tag_name)
        
        if operation == "create":
            if message:
                run_git_command(["git", "tag", "-a", tag_name, "-m", message], config)
            else:
                run_git_command(["git", "tag", tag_name], config)
        elif operation == "delete":
            run_git_command(["git", "tag", "-d", tag_name], config)
        elif operation == "push":
            run_git_command(["git", "push", "origin", tag_name], config)
    except GitError as e:
        raise GitError(f"Failed to {operation} tag: {str(e)}") from e

def manage_stash(
    operation: Literal["save", "pop", "apply", "drop", "list"],
    message: Optional[str] = None,
    stash_id: Optional[str] = None,
    config: OptionalConfig = None
) -> Optional[str]:
    """Manage git stash operations.
    
    Args:
        operation: The operation to perform
        message: Stash message (for save operation)
        stash_id: Stash identifier (for pop, apply, drop operations)
        config: GitConfig instance containing configuration options
        
    Returns:
        Optional[str]: Stash list output for list operation
        
    Raises:
        GitError: If the stash operation fails
    """
    try:
        if config and config.verbose:
            debug_item(f"Stash operation: {operation}", f"{message or ''} {stash_id or ''}")
        
        if operation == "save":
            cmd = ["git", "stash", "push"]
            if message:
                cmd.extend(["-m", message])
            run_git_command(cmd, config)
        elif operation == "pop":
            cmd = ["git", "stash", "pop"]
            if stash_id:
                cmd.append(stash_id)
            run_git_command(cmd, config)
        elif operation == "apply":
            cmd = ["git", "stash", "apply"]
            if stash_id:
                cmd.append(stash_id)
            run_git_command(cmd, config)
        elif operation == "drop":
            if not stash_id:
                raise GitError("Stash ID is required for drop operation")
            run_git_command(["git", "stash", "drop", stash_id], config)
        elif operation == "list":
            stdout, _ = run_git_command(["git", "stash", "list"], config)
            return stdout
    except GitError as e:
        raise GitError(f"Failed to {operation} stash: {str(e)}") from e
    return None

def analyze_commit_patterns(commits: List[Dict[str, str]], config: OptionalConfig = None) -> Dict[str, Dict[str, int]]:
    """Analyze commit history to find patterns in commit types and scopes.
    
    Args:
        commits: List of commit dictionaries with hash, message, author, date
        config: GitConfig instance containing configuration options
        
    Returns:
        Dict[str, Dict[str, int]]: Dictionary containing frequency counts of commit types and scopes
    """
    if config and config.verbose:
        debug_header("Analyzing commit patterns")
        debug_item("Number of commits", str(len(commits)))
    
    patterns = {
        'types': Counter(),  # Count of commit types (feat, fix, etc.)
        'scopes': Counter()  # Count of commit scopes (in parentheses)
    }
    
    for commit in commits:
        message = commit.get('message', '')
        if not message:
            continue
            
        # Extract commit type (everything before the colon)
        if ':' in message:
            type_part = message.split(':', 1)[0].strip()
            # Remove emoji if present
            type_part = type_part.split(' ', 1)[0].strip()
            patterns['types'][type_part.lower()] += 1
            
            if config and config.verbose:
                debug_item("Found commit type", type_part)
        
        # Extract scope (text in parentheses)
        if '(' in message and ')' in message:
            scope = message[message.find('(') + 1:message.find(')')].strip()
            if scope:
                patterns['scopes'][scope.lower()] += 1
                if config and config.verbose:
                    debug_item("Found commit scope", scope)
    
    if config and config.verbose:
        debug_item("Commit types found", str(dict(patterns['types'])))
        debug_item("Commit scopes found", str(dict(patterns['scopes'])))
    
    return patterns

def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful interruption of git operations."""
    def signal_handler(signum, frame):
        """Handle interrupt signals by unstaging files and exiting gracefully."""
        unstage_files()
        rprint(Panel(
            "Operation cancelled by user.",
            title="Cancelled",
            border_style="yellow"
        ))
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
