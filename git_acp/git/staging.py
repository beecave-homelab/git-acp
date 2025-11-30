from __future__ import annotations

import shlex
import signal
import sys

from rich import print as rprint
from rich.console import Console
from rich.panel import Panel

from git_acp.config import DEFAULT_REMOTE
from git_acp.utils import OptionalConfig, debug_header, debug_item, status, success
from .core import GitError, run_git_command

console = Console()


def get_current_branch(config: OptionalConfig = None) -> str:
    """Get the name of the current git branch."""
    try:
        if config and config.verbose:
            debug_header("Getting Current Branch")
        stdout, _ = run_git_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], config
        )
        if not stdout:
            raise GitError(
                "Failed to determine current branch. Are you in a valid git repository?"
            )
        if config and config.verbose:
            debug_item("Current Branch", stdout)
        return stdout
    except GitError as e:
        if config and config.verbose:
            debug_header("Branch Detection Failed")
            debug_item("Error", str(e))
        raise GitError(
            "Could not determine the current branch. Please ensure you're in a git repository."
        ) from e


def git_add(files: str, config: OptionalConfig = None) -> None:
    """Add files to git staging area."""
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
    """Commit staged changes to the repository."""
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
    """Push committed changes to the remote repository."""
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
            raise GitError(
                f"Push rejected. Please pull the latest changes first: git pull {DEFAULT_REMOTE} {branch}"
            ) from e
        elif "no upstream branch" in str(e).lower():
            raise GitError(
                f"No upstream branch. Set the remote with: git push --set-upstream {DEFAULT_REMOTE} {branch}"
            ) from e
        else:
            raise GitError(f"Failed to push changes: {str(e)}") from e


def unstage_files(config: OptionalConfig = None) -> None:
    """Unstage all files from the staging area."""
    try:
        if config and config.verbose:
            debug_header("Unstaging all files")
        run_git_command(["git", "reset", "HEAD"], config)
    except GitError as e:
        raise GitError(f"Failed to unstage files: {str(e)}") from e


def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful interruption of git operations."""

    def signal_handler(signum, frame):
        unstage_files()
        rprint(
            Panel(
                "Operation cancelled by user.", title="Cancelled", border_style="yellow"
            )
        )
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
