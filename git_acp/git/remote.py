"""Manage remote repository operations."""

from git_acp.git.runner import run_git_command, GitError


def manage_remote(
    operation: str, remote_name: str, url: str = None, config=None
) -> None:
    """
    Manage git remotes.

    Args:
        operation: "add", "remove", or "set-url".
        remote_name: The remote's name.
        url: The remote URL (required for add and set-url).
    """
    if operation == "add":
        if not url:
            raise GitError("URL is required for adding a remote.")
        run_git_command(["git", "remote", "add", remote_name, url], config)
    elif operation == "remove":
        run_git_command(["git", "remote", "remove", remote_name], config)
    elif operation == "set-url":
        if not url:
            raise GitError("URL is required for setting remote URL.")
        run_git_command(["git", "remote", "set-url", remote_name, url], config)
