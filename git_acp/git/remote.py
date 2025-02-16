"""Git remote operations."""

from git_acp.git.exceptions import GitError
from git_acp.git.core import run_git_command


def add_remote(name: str, url: str, config=None) -> None:
    """Add a new remote.

    Args:
        name: Remote name
        url: Remote URL
        config: Optional configuration

    Raises:
        GitError: If adding remote fails
    """
    try:
        run_git_command(["git", "remote", "add", name, url], config)
    except Exception as e:
        raise GitError(f"Failed to add remote: {str(e)}") from e


def remove_remote(name: str, config=None) -> None:
    """Remove a remote.

    Args:
        name: Remote name
        config: Optional configuration

    Raises:
        GitError: If removing remote fails
    """
    try:
        run_git_command(["git", "remote", "remove", name], config)
    except Exception as e:
        raise GitError(f"Failed to remove remote: {str(e)}") from e


def get_remote_url(name: str = "origin", config=None) -> str:
    """Get the URL of a remote.

    Args:
        name: Remote name
        config: Optional configuration

    Returns:
        str: Remote URL

    Raises:
        GitError: If getting remote URL fails
    """
    try:
        stdout, _ = run_git_command(["git", "remote", "get-url", name], config)
        return stdout
    except Exception as e:
        raise GitError(f"Failed to get remote URL: {str(e)}") from e
