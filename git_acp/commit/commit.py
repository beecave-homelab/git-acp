"""Git commit workflow: adding, committing, and pushing changes."""

from typing import List
import glob

from rich.console import Console

from git_acp.git import run_git_command, GitError
from git_acp.utils import debug_header, debug_item, success, status
from git_acp.config import GIT_SETTINGS

console = Console()


def git_add(files: str | List[str], config=None) -> None:
    """Add files to git staging area.

    Args:
        files: A string or list of strings with file paths or glob patterns
        config: Optional configuration object
    """
    try:
        if not isinstance(files, list):
            files = [files]

        # Track if any files were actually added
        files_added = False

        for pattern in files:
            # First try to expand the glob pattern
            expanded_files = glob.glob(pattern)

            if expanded_files:
                # If glob pattern matched files, add each one
                for file in expanded_files:
                    cmd = ["git", "add", "--", file]
                    if config and config.verbose:
                        debug_item(config, "Command", " ".join(cmd))
                    run_git_command(cmd, config)
                    files_added = True
            else:
                # If glob didn't match, try adding the pattern directly
                # This handles both regular files and git's own glob patterns
                cmd = ["git", "add", "--", pattern]
                if config and config.verbose:
                    debug_item(config, "Command", " ".join(cmd))
                run_git_command(cmd, config)
                files_added = True

        if files_added:
            success("Files added successfully")
        else:
            raise GitError(
                "No files matched the specified patterns",
                suggestion="Check file patterns and ensure they match existing files",
            )
    except GitError as e:
        raise GitError(f"Failed to add files: {str(e)}") from e


def git_commit(message: str, config=None) -> None:
    """Commit staged changes."""
    try:
        if config and config.verbose:
            debug_header("Committing changes")
        with status("Committing..."):
            cmd = ["git", "commit", "-m", message]
            if config and config.verbose:
                debug_item(config, "Command", " ".join(cmd))
            run_git_command(cmd, config)
        success("Changes committed successfully")
    except GitError as e:
        raise GitError(f"Failed to commit changes: {str(e)}") from e


def git_push(branch: str, config=None) -> None:
    """Push changes to remote repository."""
    try:
        if config and config.verbose:
            debug_header("Pushing changes")
        with status(f"Pushing to {branch}..."):
            cmd = ["git", "push", GIT_SETTINGS["default_remote"], branch]
            if config and config.verbose:
                debug_item(config, "Command", " ".join(cmd))
            run_git_command(cmd, config)
        success("Changes pushed successfully")
    except GitError as e:
        raise GitError(f"Failed to push changes: {str(e)}") from e
