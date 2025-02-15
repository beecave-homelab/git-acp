"""Git commit workflow: adding, committing, and pushing changes."""

from typing import List, Optional
import glob

from rich.console import Console

from git_acp.git import run_git_command, GitError
from git_acp.utils.formatting import (
    debug_header,
    debug_item,
    ProgressReporter,
)
from git_acp.config import GIT_SETTINGS

console = Console()


def _get_progress(
    config, progress: Optional[ProgressReporter] = None
) -> ProgressReporter:
    """Get or create a ProgressReporter instance.

    Args:
        config: Configuration object that may contain verbose setting
        progress: Optional existing ProgressReporter instance

    Returns:
        ProgressReporter: Either the provided instance or a new one
    """
    if progress is not None:
        return progress
    return ProgressReporter(verbose=config.verbose if config else False)


def git_add(
    files: str | List[str], config=None, progress: Optional[ProgressReporter] = None
) -> None:
    """Add files to git staging area.

    Args:
        files: A string or list of strings with file paths or glob patterns
        config: Optional configuration object
        progress: Optional progress reporter for status updates
    """
    progress = _get_progress(config, progress)
    try:
        if not isinstance(files, list):
            files = [files]

        # Track if any files were actually added
        files_added = False
        added_files = []
        progress.start_stage("Adding files to staging area...")

        for pattern in files:
            # First try to expand the glob pattern
            expanded_files = glob.glob(pattern)

            if expanded_files:
                # If glob pattern matched files, add each one individually
                for file in expanded_files:
                    cmd = ["git", "add", "--", file]
                    if config and config.verbose:
                        debug_item(config, "Command", " ".join(cmd))
                    run_git_command(cmd, config)
                    files_added = True
                    added_files.append(file)
            else:
                # If glob didn't match, try adding the pattern directly
                # This handles both regular files and git's own glob patterns
                cmd = ["git", "add", "--", pattern]
                if config and config.verbose:
                    debug_item(config, "Command", " ".join(cmd))
                run_git_command(cmd, config)
                files_added = True
                added_files.append(pattern)

        if files_added:
            files_list = "\n".join(f"  • {file}" for file in added_files)
            progress.end_stage(f"Added files:\n{files_list}")
        else:
            raise GitError(
                "No files matched the specified patterns",
                suggestion="Check file patterns and ensure they match existing files",
            )
    except GitError as e:
        progress.end_stage(f"Failed to add files: {str(e)}")
        raise GitError(f"Failed to add files: {str(e)}") from e


def git_commit(
    message: str, config=None, progress: Optional[ProgressReporter] = None
) -> None:
    """Commit staged changes.

    Args:
        message: Commit message
        config: Optional configuration object
        progress: Optional progress reporter for status updates
    """
    progress = _get_progress(config, progress)
    try:
        if config and config.verbose:
            debug_header("Committing changes")

        progress.start_stage("Committing changes...")
        cmd = ["git", "commit", "-m", message]
        if config and config.verbose:
            debug_item(config, "Command", " ".join(cmd))
        run_git_command(cmd, config)
        progress.end_stage("Changes committed successfully")
    except GitError as e:
        progress.end_stage(f"Failed to commit changes: {str(e)}")
        raise GitError(f"Failed to commit changes: {str(e)}") from e


def git_push(
    branch: str, config=None, progress: Optional[ProgressReporter] = None
) -> None:
    """Push changes to remote repository.

    Args:
        branch: Branch to push to
        config: Optional configuration object
        progress: Optional progress reporter for status updates
    """
    progress = _get_progress(config, progress)
    try:
        if config and config.verbose:
            debug_header("Pushing changes")

        progress.start_stage(f"Pushing to {branch}...")
        cmd = ["git", "push", GIT_SETTINGS["default_remote"], branch]
        if config and config.verbose:
            debug_item(config, "Command", " ".join(cmd))
        run_git_command(cmd, config)
        progress.end_stage("Changes pushed successfully")
    except GitError as e:
        progress.end_stage(f"Failed to push changes: {str(e)}")
        raise GitError(f"Failed to push changes: {str(e)}") from e
