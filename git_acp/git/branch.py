"""Git branch operations."""

import time

from git_acp.git.exceptions import GitError
from git_acp.git.core import run_git_command
from git_acp.utils.formatting import warning


def get_current_branch() -> str:
    """Get the name of the current git branch.

    Returns:
        str: Current branch name

    Raises:
        GitError: If getting current branch fails
    """
    try:
        stdout, _ = run_git_command(["git", "branch", "--show-current"])
        if not stdout:
            raise GitError(
                "Not on any branch",
                suggestion="Check if you are in a detached HEAD state",
            )
        return stdout
    except Exception as e:
        raise GitError(f"Failed to get current branch: {str(e)}") from e


def get_default_branch() -> str:
    """Get the default branch name (usually main or master).

    Returns:
        str: Default branch name

    Raises:
        GitError: If getting default branch fails
    """
    try:
        # Try to get the default branch from origin
        stdout, _ = run_git_command(["git", "symbolic-ref", "refs/remotes/origin/HEAD"])
        if stdout:
            return stdout.rsplit("/", maxsplit=1)[-1]

        # Fallback to checking local branches
        stdout, _ = run_git_command(["git", "branch"])
        branches = [b.strip("* ") for b in stdout.split("\n") if b.strip()]

        # Check for common default branch names
        for name in ["main", "master"]:
            if name in branches:
                return name

        # If no common names found, use the first branch
        if branches:
            return branches[0]

        raise GitError(
            "No default branch found",
            suggestion="Initialize repository with a branch first",
        )
    except Exception as e:
        raise GitError(f"Failed to get default branch: {str(e)}") from e


def create_branch(branch_name: str, config=None) -> None:
    """Create a new branch."""
    run_git_command(["git", "checkout", "-b", branch_name], config)


def delete_branch(branch_name: str, force: bool = False, config=None) -> None:
    """Delete an existing branch."""
    if force:
        run_git_command(["git", "branch", "-D", branch_name], config)
    else:
        run_git_command(["git", "branch", "-d", branch_name], config)


def merge_branch(source_branch: str, config=None) -> None:
    """Merge a branch into the current branch."""
    run_git_command(["git", "merge", source_branch], config)


def get_branch_age(branch_name: str) -> int:
    """Get the age of a branch in days."""
    try:
        # Get stdout from command execution
        stdout, _ = run_git_command(
            ["git", "log", "-1", "--format=%ct", "--", branch_name]
        )

        if not stdout:
            return 0

        commit_time = int(stdout.strip())
        return (int(time.time()) - commit_time) // 86400

    except (GitError, ValueError) as e:
        warning(f"Failed to get branch age: {str(e)}")
        return 0


def find_parent_branch() -> str:
    """Find parent branch using git merge-base.

    Returns:
        Name of parent branch

    Raises:
        GitError: If parent detection fails
    """
    try:
        current_branch = get_current_branch()
        default_branch = get_default_branch()

        # Find merge base with default branch
        stdout, _ = run_git_command(
            ["git", "merge-base", current_branch, default_branch]
        )
        merge_base = stdout.strip()

        # Find branches containing the merge base
        stdout, _ = run_git_command(
            ["git", "branch", "--contains", merge_base, "--format=%(refname:short)"]
        )
        branches = [b.strip() for b in stdout.splitlines() if b.strip()]

        # Exclude current branch and prefer default branch
        for branch in branches:
            if branch == default_branch:
                return default_branch
            if branch != current_branch:
                return branch

        return default_branch  # Fallback

    except Exception as e:
        raise GitError(f"Failed to find parent branch: {str(e)}") from e
