"""Git commit workflow: adding, committing, and pushing changes."""

from rich.console import Console
from rich.panel import Panel
from git_acp.git.runner import run_git_command, GitError
from git_acp.utils import debug_header, debug_item, success, status

console = Console()


def git_add(files: str, config=None) -> None:
    """Stage files for commit."""
    try:
        debug_header("Staging files")
        if files == ".":
            run_git_command(["git", "add", "."], config)
        else:
            import shlex

            for file in shlex.split(files):
                run_git_command(["git", "add", file], config)
        success("Files added successfully")
    except GitError as e:
        raise GitError(f"Failed to add files: {str(e)}") from e


def git_commit(message: str, config=None) -> None:
    """Commit staged changes."""
    try:
        debug_header("Committing changes")
        with status("Committing..."):
            run_git_command(["git", "commit", "-m", message], config)
        success("Changes committed successfully")
    except GitError as e:
        raise GitError(f"Failed to commit changes: {str(e)}") from e


def git_push(branch: str, config=None) -> None:
    """Push changes to remote repository."""
    from git_acp.config.settings import GIT_SETTINGS

    try:
        debug_header("Pushing changes")
        with status(f"Pushing to {branch}..."):
            run_git_command(
                ["git", "push", GIT_SETTINGS["default_remote"], branch], config
            )
        success("Changes pushed successfully")
    except GitError as e:
        raise GitError(f"Failed to push changes: {str(e)}") from e
